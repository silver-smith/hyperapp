import logging
from collections import namedtuple
from functools import cached_property
from operator import attrgetter

from hyperapp.common.htypes import ref_str

from . import htypes
from .services import (
    mosaic,
    resource_module_factory,
    web,
    )
from .code.dep import CodeDep, FixturesDep, ServiceDep
from .code.import_task import AttrCallTask, AttrEnumTask, ImportTask
from .code.scaffolds import (
    discoverer_module_res,
    function_call_res,
    invite_attr_constructors,
    recorder_module_res,
    test_call_res,
    )

log = logging.getLogger(__name__)


ImportsInfo = namedtuple('ImportsInfo', 'used_types want_deps test_services test_code')


def _enum_resource_module_deps(resource_module):
    for module_name, var_name in resource_module.used_imports:
        l = var_name.split('.')
        if len(l) == 2 and l[1] == 'service':
            yield ServiceDep(l[0])
        if len(l) > 1 and l[-1] == 'module':
            code_name = '.'.join(l[:-1])
            yield CodeDep(code_name)


def _enum_provided_services(attr_list):
    for attr in attr_list:
        for ctr_ref in attr.constructors:
            ctr = web.summon(ctr_ref)
            if isinstance(ctr, htypes.attr_constructors.service):
                yield ctr.name


def _imports_info(imports):
    used_types = set()
    want_deps = set()
    test_services = set()
    test_code = set()
    for imp in imports:
        if imp[-1] == 'shape':
            imp = imp[:-1]  # Revert pycharm debugger mangle.
        if len(imp) < 2:
            continue
        kind, name, *_ = imp
        if kind == 'htypes':
            if len(imp) < 3:
                continue
            _, type_module, type_name, *_ = imp
            used_types.add((type_module, type_name))
            continue
        if kind == 'services':
            want_deps.add(ServiceDep(name))
            continue
        if kind == 'code':
            want_deps.add(CodeDep(name))
            continue
        if kind == 'tested':
            if len(imp) < 3:
                continue
            _, kind, name, *_ = imp
            if kind == 'services':
                test_services.add(name)
                continue
            if kind == 'code':
                test_code.add(name)
                continue
        raise RuntimeError(f"Unknown import kind %r: %s", kind, '.'.join(imp))
    log.info("Discovered import deps: %s", want_deps)
    log.info("Discovered test_services: %s", test_services)
    log.info("Discovered test_code: %s", test_code)

    return ImportsInfo(
        used_types=used_types,
        want_deps=want_deps,
        test_services=test_services,
        test_code=test_code,
        )


class Unit:

    def __init__(self, ctx, generator_ref, root_dir, path):
        self._ctx = ctx
        self._generator_ref = generator_ref
        self._source_path = path
        self._stem = path.name[:-len('.dyn.py')]
        self.code_name = self._stem
        rel_dir = path.parent.relative_to(root_dir)
        self._dir = str(rel_dir).replace('/', '.')
        self.name = f'{self._dir}.{self._stem}'
        self._resources_path = path.with_name(self._stem + '.resources.yaml')
        self._current_source_ref_str = None
        self._resource_module = None
        self._import_set = None
        self._attr_list = None  # inspect.attr|fn_attr|generator_fn_attr list
        self._attr_called = False
        self._tests = set()  # TestsUnit set

    def __repr__(self):
        return f"<Unit {self.name!r}>"

    @cached_property
    def is_fixtures(self):
        return False

    @cached_property
    def is_tests(self):
        return False

    def _set_providers(self, graph, provide_services):
        for service_name in provide_services:
            dep = ServiceDep(service_name)
            try:
                provider = graph.dep_to_provider[dep]
            except KeyError:
                pass
            else:
                raise RuntimeError(f"More than one module provide service {service_name!r}: {provider!r} and {self!r}")
            graph.dep_to_provider[dep] = self
            log.debug("%s: Provide service: %r", self.name, service_name)

    def init(self, graph):
        graph.dep_to_provider[CodeDep(self._stem)] = self
        if not self._resources_path.exists():
            log.info("%s: missing", self.name)
            return
        resource_module = resource_module_factory(self._ctx.resource_registry, self.name, self._resources_path)
        if not resource_module.is_auto_generated:
            self._resource_module = resource_module
            self._ctx.resource_registry.set_module(self.name, resource_module)
            self._set_providers(graph, resource_module.provided_services)
            log.info("%s: manually generated", self.name)
            return
        self._current_source_ref_str = resource_module.source_ref_str
        deps = list(_enum_resource_module_deps(resource_module))
        if self._hash_matches(graph, deps):
            self._resource_module = resource_module
            self._ctx.resource_registry.set_module(self.name, resource_module)
            self._set_providers(graph, resource_module.provided_services)
            log.info("%s: Up-to-date, provides: %s", self.name, resource_module.provided_services)

    def resource(self, name):
        return self._ctx.resource_registry[self.name, name]

    def provided_dep_resource(self, dep):
        return self.resource(dep.resource_name)

    def pick_service_resource(self, module_res, service_name):
        assert self._attr_list is not None  # Not yet imported/attr enumerated.
        name_to_res = {}
        ass_list = invite_attr_constructors(self._ctx, self._attr_list, module_res, name_to_res)
        for name, resource in name_to_res.items():
            if name.endswith('.service'):
                sn, _ = name.rsplit('.', 1)
                if sn == service_name:
                    return (ass_list, resource)
        raise RuntimeError(f"{self}: Service {service_name!r} was not created by it's constructor")

    def make_module_res(self, import_list):
        return htypes.builtin.python_module(
            module_name=self._stem,
            source=self._source_path.read_text(),
            file_path=str(self._source_path),
            import_list=tuple(import_list),
            )

    def _make_source_ref(self, dep_units):
        deps = [
            u.source_dep_record for u in
            sorted([self, *dep_units], key=attrgetter('name'))
            ]
        return mosaic.put(htypes.rc.module_deps(deps))

    @cached_property
    def source_dep_record(self):
        source_ref = mosaic.put(self._source_path.read_bytes())
        return htypes.rc.source_dep(self.name, source_ref)

    def _hash_matches(self, graph, deps):
        if not self._current_source_ref_str:
            return False
        dep_units = []
        for dep in deps:
            try:
                module = graph.dep_to_provider[dep]
            except KeyError:
                log.debug("%s: dep %s is missing", self.name, dep)
                return False
            if not module.is_up_to_date(graph):
                log.debug("%s: dep %s module %s is outdated", self.name, dep, module)
                return False
            dep_units.append(module)
        source_ref = self._make_source_ref(dep_units)
        return ref_str(source_ref) == self._current_source_ref_str

    def is_up_to_date(self, graph):
        if self._resource_module:
            return True
        return self._hash_matches(graph, graph.name_to_deps[self.name])

    def deps_are_ready(self, graph):
        for dep in graph.name_to_deps[self.name]:
            try:
                provider = graph.dep_to_provider[dep]
            except KeyError:
                return False
            if not provider.is_up_to_date(graph):
                return False
        return True

    def report_deps(self, graph):
        for dep in graph.name_to_deps[self.name]:
            try:
                provider = graph.dep_to_provider[dep]
            except KeyError:
                log.info("%s: Dep %s has no provider", self.name, dep)
            else:
                if not provider.is_up_to_date(graph):
                    log.info("%s: Dep %s provider %s is not ready", self.name, dep, provider)

    def add_test(self, unit):
        self._tests.add(unit)
        log.info("%s is tested by %s", self.name, unit.name)

    def _fixtures_unit(self, graph):
        return graph.dep_to_provider.get(FixturesDep(self.name))

    def _make_call_attr_tasks(self, graph):
        fixtures = self._fixtures_unit(graph)
        task_list = []
        for attr in self._attr_list:
            if not isinstance(attr, htypes.inspect.fn_attr):
                continue
            recorders_and_call_res = function_call_res(graph, self._ctx, self, fixtures, attr)
            if not recorders_and_call_res:
                continue  # No param fixtures.
            recorders, call_res = recorders_and_call_res
            task = AttrCallTask(self, attr.name, recorders, call_res)
            task_list.append(task)
        return task_list

    def make_tasks(self, graph):
        if self._import_set is None:
            recorders, module_res = discoverer_module_res(self._ctx, self)
            return [ImportTask(self, recorders, module_res)]
        if not self.deps_are_ready(graph):
            return []
        if self._attr_list is None:
            # Got incomplete error when collecting attributes, retry with complete imports:
            recorders, module_res = recorder_module_res(graph, self._ctx, self)
            return [AttrEnumTask(self, recorders, module_res)]
        if not self._attr_called:
            return self._make_call_attr_tasks(graph)
        # Already imported and attributes collected and called.
        return []

    def _update_imports_deps(self, graph, import_set):
        info = _imports_info(import_set)
        graph.name_to_deps[self.name] |= info.want_deps
        return info

    def set_imports(self, graph, import_set):
        self._import_set = import_set
        self._update_imports_deps(graph, import_set)

    def add_imports(self, graph, import_set):
        self._import_set |= import_set
        self._update_imports_deps(graph, import_set)

    def set_attributes(self, graph, attr_list):
        self._attr_list = attr_list
        self._set_providers(graph, _enum_provided_services(attr_list))

    def set_attr_called(self):
        self._attr_called = True


class FixturesDepsProviderUnit(Unit):

    def __init__(self, ctx, generator_ref, root_dir, path):
        super().__init__(ctx, generator_ref, root_dir, path)
        self._provided_deps = set()

    def _set_providers(self, graph, provide_services):
        self._provided_deps = {
            ServiceDep(service_name) for service_name in provide_services
            }

    @property
    def provided_deps(self):
        return self._provided_deps


class FixturesUnit(FixturesDepsProviderUnit):

    def __repr__(self):
        return f"<FixturesUnit {self.name!r}>"

    @cached_property
    def is_fixtures(self):
        return True

    @cached_property
    def _target_unit_name(self):
        l = self._stem.split('.')
        assert l[-1] == 'fixtures'
        return self._dir + '.' + '.'.join(l[:-1])

    def init(self, graph):
        super().init(graph)
        dep = FixturesDep(self._target_unit_name)
        graph.name_to_deps[self._target_unit_name].add(dep)
        graph.dep_to_provider[dep] = self


class TestsUnit(FixturesDepsProviderUnit):

    def __init__(self, ctx, generator_ref, root_dir, path):
        super().__init__(ctx, generator_ref, root_dir, path)
        self._tested_units = None  # Unit list
        self._tested_services = None  # str list

    def __repr__(self):
        return f"<TestsUnit {self.name!r}>"

    @cached_property
    def is_tests(self):
        return True

    def report_deps(self, graph):
        super().report_deps(graph)
        if self._tested_services is None:
            log.info("%s: Tested service list is not yet discovered", self.name)
        else:
            for service_name in self._tested_services:
                dep = ServiceDep(service_name)
                if dep not in graph.dep_to_provider:
                    log.info("%s: tested %s has no provider", self.name, dep)

    def _set_providers(self, graph, provide_services):
        pass

    def _tested_services_modules(self, graph):
        service_to_unit = {}
        for service_name in self._tested_services:
            dep = ServiceDep(service_name)
            provider = graph.dep_to_provider.get(dep)
            if provider:
                log.debug("%s: service %s provider: %s", self.name, service_name, provider)
                service_to_unit[service_name] = provider
            else:
                log.debug("%s: service %s provider is not yet discovered", self.name, service_name)
                return None
        return service_to_unit  # str -> unit

    def _make_call_attr_tasks(self, graph):
        if not all(unit.deps_are_ready(graph) for unit in self._tested_units):
            return []
        tested_service_to_unit = self._tested_services_modules(graph)
        if tested_service_to_unit is None:
            # Not all service providers are yet discovered.
            return []
        if not all(unit.deps_are_ready(graph) for unit in tested_service_to_unit.values()):
            return []
        task_list = []
        for attr in self._attr_list:
            if not isinstance(attr, htypes.inspect.fn_attr):
                continue
            if not attr.name.startswith('test'):
                continue
            recorders, call_res = test_call_res(graph, self._ctx, self, self._tested_units, tested_service_to_unit, attr)
            task = AttrCallTask(self, attr.name, recorders, call_res)
            task_list.append(task)
        return task_list

    def _update_imports_deps(self, graph, import_set):
        info = super()._update_imports_deps(graph, import_set)
        self._tested_units = []
        for name in info.test_code:
            for unit in graph.name_to_unit.values():
                if unit.code_name == name:
                    unit.add_test(self)
                    self._tested_units.append(unit)
                    break
            else:
                raise RuntimeError(f"{self.name}: Unknown tested code module: {name}")
        self._tested_services = info.test_services
