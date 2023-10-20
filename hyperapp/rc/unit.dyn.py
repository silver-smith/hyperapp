import asyncio
import logging
from collections import defaultdict, namedtuple
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
from .code import import_driver, call_driver
from .code.scaffolds import (
    discoverer_module_res,
    enum_dep_imports,
    function_call_res,
    invite_attr_constructors,
    recorder_module_res,
    test_call_res,
    types_import_list,
    )

log = logging.getLogger(__name__)


ResModuleInfo = namedtuple('DesModuleInfo', 'want_deps test_code test_services')
ImportsInfo = namedtuple('ImportsInfo', 'used_types want_deps test_code test_services')


def _recorder_piece_list(recorders):
    piece_list = []
    for module_name, recorder_list in recorders.items():
        for rec in recorder_list:
            import_recorder = htypes.inspect.import_recorder(module_name, rec)
            piece_list.append(import_recorder)
    return piece_list


def _module_import_list_to_dict(module_import_list):
    module_name_to_imports = defaultdict(set)
    for rec in module_import_list:
        module_name_to_imports[rec.module] |= set(rec.imports)
    return module_name_to_imports


def _resource_module_info(resource_module, code_module_name):
    want_deps = set()
    for module_name, var_name in resource_module.used_imports:
        l = var_name.split('.')
        if len(l) == 2 and l[1] == 'service':
            want_deps.add(ServiceDep(l[0]))
        if len(l) > 1 and l[-1] == 'module':
            code_name = '.'.join(l[:-1])
            want_deps.add(CodeDep(code_name))
    test_code = set()
    test_services = set()
    import_list = resource_module.code_module_imports(code_module_name)
    for name in import_list:
        l = name.split('.')
        if len(l) != 3:
            continue
        do, what, name = l
        if do != 'tested':
            continue
        if what == 'code':
            test_code.add(name)
        if what == 'services':
            test_services.add(name)
    return ResModuleInfo(
        want_deps=want_deps,
        test_code=test_code,
        test_services=test_services,
        )


def _enum_provided_services(attr_list):
    for attr in attr_list:
        for ctr_ref in attr.constructors:
            ctr = web.summon(ctr_ref)
            if isinstance(ctr, htypes.attr_constructors.service):
                yield ctr.name


def _imports_info(imports):
    used_types = set()
    want_deps = set()
    test_code = set()
    test_services = set()
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
        test_code=test_code,
        test_services=test_services,
        )


async def _lock_and_notify_all(condition):
    async with condition:
        condition.notify_all()


class Unit:

    _providers_changed = asyncio.Condition()
    _test_targets_discovered = asyncio.Condition()
    _unit_constructed = asyncio.Condition()

    def __init__(self, graph, ctx, generator_ref, root_dir, path):
        self._graph = graph
        self._ctx = ctx
        self._generator_ref = generator_ref
        self._source_path = path
        self._stem = path.name[:-len('.dyn.py')]
        self.code_name = self._stem
        rel_dir = path.parent.relative_to(root_dir)
        self._dir = str(rel_dir).replace('/', '.')
        self.name = f'{self._dir}.{self._stem}'
        self._resources_path = path.with_name(self._stem + '.resources.yaml')
        self._is_up_to_date = False
        # self._deps = None
        self._resource_module = None
        self._tests = set()  # TestsUnit set

    def __repr__(self):
        return f"<Unit {self.name!r}>"

    @property
    def is_builtins(self):
        return False

    @property
    def is_fixtures(self):
        return False

    @property
    def is_tests(self):
        return False

    @property
    def is_up_to_date(self):
        return self._is_up_to_date

    @property
    def is_imports_discovered(self):
        return self._import_set is not None

    def report_deps(self):
        pass

    @cached_property
    def source_dep_record(self):
        source_ref = mosaic.put(self._source_path.read_bytes())
        return htypes.rc.source_dep(self.name, source_ref)

    def _make_source_ref(self, dep_units):
        deps = [
            u.source_dep_record for u in
            sorted([self, *dep_units], key=attrgetter('name'))
            ]
        return mosaic.put(htypes.rc.module_deps(deps))

    def _deps_hash_str(self, dep_set):
        dep_units = set()
        for dep in dep_set:
            try:
                unit = self._graph.dep_to_provider[dep]
            except KeyError:
                log.debug("%s: dep %s is missing", self.name, dep)
                return False
            if unit.is_builtins:
                continue
            if not unit.is_up_to_date:
                log.debug("%s: dep %s %s is outdated", self.name, dep, unit)
                return False
            dep_units.add(unit)
        source_ref = self._make_source_ref(dep_units)
        return ref_str(source_ref)

    async def _set_service_providers(self, provide_services):
        for service_name in provide_services:
            dep = ServiceDep(service_name)
            try:
                provider = self._graph.dep_to_provider[dep]
            except KeyError:
                pass
            else:
                raise RuntimeError(f"More than one module provide service {service_name!r}: {provider!r} and {self!r}")
            self._graph.dep_to_provider[dep] = self
            log.debug("%s: Provide service: %r", self.name, service_name)
        await _lock_and_notify_all(self._providers_changed)

    async def _imports_discovered(self, info):
        pass

    def init(self):
        self._graph.dep_to_provider[CodeDep(self.code_name)] = self
        if not self._resources_path.exists():
            return
        self._resource_module = resource_module_factory(self._ctx.resource_registry, self.name, self._resources_path)
        if self._resource_module.is_auto_generated:
            return
        self._ctx.resource_registry.set_module(self.name, self._resource_module)
        self._is_up_to_date = True
        log.info("%s: manually generated", self.name)
        return

    def make_module_res(self, import_list):
        return htypes.builtin.python_module(
            module_name=self._stem,
            source=self._source_path.read_text(),
            file_path=str(self._source_path),
            import_list=tuple(import_list),
            )

    async def _wait_for_all_test_targets(self):
        async with self._test_targets_discovered:
            while True:
                for unit in self._graph.name_to_unit.values():
                    if unit.is_tests and not unit.targets_discovered:
                        break
                else:
                    return
                await self._test_targets_discovered.wait()

    async def _wait_for_providers(self, dep_set):
        async with self._providers_changed:
            while True:
                unknown = [dep for dep in dep_set if dep not in self._graph.dep_to_provider]
                if not unknown:
                    return
                log.debug("%s: Unknown providers for deps: %s", self.name, unknown)
                await self._providers_changed.wait()

    async def _wait_for_deps(self, dep_set):
        await self._wait_for_providers(dep_set)
        async with self._unit_constructed:
            while True:
                providers = {self._graph.dep_to_provider[dep] for dep in dep_set}
                outdated = [p for p in providers if not p.is_up_to_date]
                if not outdated:
                    return
                log.debug("%s: Outdated providers: %s", self.name, outdated)
                await self._unit_constructed.wait()

    async def _import_module(self, process_pool, recorders, module_res):
        result = await process_pool.run(
            import_driver.import_module,
            import_recorders=_recorder_piece_list(recorders),
            module_ref=mosaic.put(module_res),
            )
        imports_dict = _module_import_list_to_dict(result.imports)
        imports = imports_dict[self.name]
        info = _imports_info(imports)
        return (result, info)

    async def _discover_attributes(self, process_pool):
        log.info("%s: discover imports", self.name)
        recorders, module_res = discoverer_module_res(self._ctx, self)
        result, info = await self._import_module(process_pool, recorders, module_res)
        await self._imports_discovered(info)
        while result.error:
            error = web.summon(result.error)
            if not isinstance(error, htypes.import_discoverer.using_incomplete_object):
                raise error
            log.info("%s: Incomplete object: %s", self.name, error.message)
            await self._wait_for_deps(info.want_deps)
            recorders, module_res = recorder_module_res(self._graph, self._ctx, self, info.want_deps)
            log.info("%s: discover attributes", self.name)
            result, info = await self._import_module(process_pool, recorders, module_res)
        attr_list = [web.summon(ref) for ref in result.attr_list]
        return info, attr_list

    async def run(self, process_pool):
        log.info("Run: %s", self)
        if not self._resource_module.is_auto_generated:
            await self._set_service_providers(self._resource_module.provided_services)
            return
        info = _resource_module_info(self._resource_module, self.code_name)
        if self._deps_hash_str(info.want_deps) == self._resource_module.source_ref_str:
            await self._set_service_providers(self._resource_module.provided_services)
            log.info("%s: sources match", self.name)
            await self._wait_for_all_test_targets()
        else:
            log.info("%s: sources does not match", self.name)
            info, attr_list = await self._discover_attributes(process_pool)
            await self._set_service_providers(_enum_provided_services(attr_list))

    def add_test(self, test_unit):
        self._tests.add(test_unit)


class FixturesDepsProviderUnit(Unit):

    def __init__(self, graph, ctx, generator_ref, root_dir, path):
        super().__init__(graph, ctx, generator_ref, root_dir, path)

    async def _set_service_providers(self, provide_services):
        pass


class FixturesUnit(FixturesDepsProviderUnit):

    def __repr__(self):
        return f"<FixturesUnit {self.name!r}>"

    @property
    def is_fixtures(self):
        return True


class TestsUnit(FixturesDepsProviderUnit):

    def __init__(self, graph, ctx, generator_ref, root_dir, path):
        super().__init__(graph, ctx, generator_ref, root_dir, path)
        self._targets_discovered = False

    def __repr__(self):
        return f"<TestsUnit {self.name!r}>"

    @property
    def is_tests(self):
        return True

    @property
    def targets_discovered(self):
        return self._targets_discovered

    async def _imports_discovered(self, info):
        for code_name in info.test_code:
            unit = self._graph.unit_by_code_name(code_name)
            unit.add_test(self)
        self._targets_discovered = True
        await _lock_and_notify_all(self._test_targets_discovered)

    async def run(self, process_pool):
        log.info("Run: %s", self)
        info, attr_list = await self._discover_attributes(process_pool)
