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
from .code import import_driver, call_driver, test_driver
from .code.scaffolds import (
    discoverer_module_res,
    enum_dep_imports,
    function_call_res,
    invite_attr_constructors,
    recorder_module_res,
    test_call_res,
    tested_services,
    tested_units,
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

    _providers_changed = asyncio.Condition()  # May be obsoleted by _deps_discovered.
    _new_deps_discovered = asyncio.Condition()
    _test_targets_discovered = asyncio.Condition()
    _test_completed = asyncio.Condition()
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
        self._resource_module = None
        self._deps_discovered = False
        self._tests = set()  # TestsUnit set
        self._attr_list = None  # inspect.attr|fn_attr|generator_fn_attr list
        self._used_types = set()

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

    def report_deps(self):
        pass

    def resource(self, name):
        return self._ctx.resource_registry[self.name, name]

    def provided_dep_resource(self, dep):
        return self.resource(dep.resource_name)

    @property
    def deps_discovered(self):
        return self._deps_discovered

    @property
    def deps(self):
        return self._graph.name_to_deps[self.name]

    @cached_property
    def source_dep_record(self):
        source_ref = mosaic.put(self._source_path.read_bytes())
        return htypes.rc.source_dep(self.name, source_ref)

    def _make_source_ref(self, units):
        deps = [
            u.source_dep_record for u in
            sorted(units, key=attrgetter('name'))
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
        source_ref = self._make_source_ref([self, *dep_units])
        return ref_str(source_ref)

    async def _set_service_providers(self, provide_services):
        for service_name in provide_services:
            dep = ServiceDep(service_name)
            try:
                provider = self._graph.dep_to_provider[dep]
            except KeyError:
                pass
            else:
                if provider is not self:
                    raise RuntimeError(f"More than one module provide service {service_name!r}: {provider!r} and {self!r}")
                else:
                    continue
            self._graph.dep_to_provider[dep] = self
            log.debug("%s: Provide service: %r", self.name, service_name)
        await _lock_and_notify_all(self._providers_changed)

    async def _imports_discovered(self, info):
        self.deps.update(info.want_deps)
        self._deps_discovered = True
        await _lock_and_notify_all(self._new_deps_discovered)

    def make_module_res(self, import_list):
        return htypes.builtin.python_module(
            module_name=self._stem,
            source=self._source_path.read_text(),
            file_path=str(self._source_path),
            import_list=tuple(import_list),
            )

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

    async def _wait_for_deps_discovered(self, units):
        async with self._new_deps_discovered:
            while True:
                not_discovered = {u for u in units if not u.deps_discovered}
                if not not_discovered:
                    return
                log.debug("%s: Deps not discovered: %s", self.name, not_discovered)
                await self._new_deps_discovered.wait()

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

    async def _wait_for_tests(self, unit_list):
        async with self._test_completed:
            while True:
                not_completed = [u for u in unit_list if not u.test_completed]
                if not not_completed:
                    return
                log.debug("%s: Waiting for tests: %s", self.name, not_completed)
                await self._test_completed.wait()

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
        await self._handle_result_imports(result.imports)
        while result.error:
            error = web.summon(result.error)
            if not isinstance(error, htypes.import_discoverer.using_incomplete_object):
                raise error
            log.info("%s: Incomplete object: %s", self.name, error.message)
            await self._wait_for_deps(self.deps | info.want_deps)
            recorders, module_res = recorder_module_res(self._graph, self._ctx, self)
            log.info("%s: discover attributes", self.name)
            # Once-imported module does not issue new import records from subsequent imports.
            result, _ = await self._import_module(process_pool, recorders, module_res)
            await self._handle_result_imports(result.imports)
        attr_list = [web.summon(ref) for ref in result.attr_list]
        return info, attr_list

    def _fixtures_unit(self):
        return self._graph.dep_to_provider.get(FixturesDep(self.name))

    async def _handle_result_imports(self, result_imports):
        imports_dict = _module_import_list_to_dict(result_imports)
        for name, imports in imports_dict.items():
            info = _imports_info(imports)
            unit = self._graph.name_to_unit[name]
            unit.add_used_types(info.used_types)

    async def _call_fn_attr(self, process_pool, attr_name, recorders, call_res):
        log.info("%s: Call attribute: %s", self.name, attr_name)
        result = await process_pool.run(
            call_driver.call_function,
            import_recorders=_recorder_piece_list(recorders),
            call_result_ref=mosaic.put(call_res),
            trace_modules=[],
            )
        await self._handle_result_imports(result.imports)

    async def _call_all_fn_attrs(self, process_pool, attr_list):
        fixtures = self._fixtures_unit()
        async with asyncio.TaskGroup() as tg:
            for attr in attr_list:
                if not isinstance(attr, htypes.inspect.fn_attr):
                    continue
                recorders_and_call_res = function_call_res(self._graph, self._ctx, self, fixtures, attr)
                if not recorders_and_call_res:
                    continue  # No param fixtures.
                recorders, call_res = recorders_and_call_res
                tg.create_task(self._call_fn_attr(process_pool, attr.name, recorders, call_res))

    async def _construct(self):
        module_res = self.make_module_res(sorted([
            *types_import_list(self._ctx, self._used_types),
            *enum_dep_imports(self._graph, self.deps),
            ]))
        resource_module = resource_module_factory(self._ctx.resource_registry, self.name)
        resource_module[f'{self.code_name}.module'] = module_res
        ass_list = invite_attr_constructors(self._ctx, self._attr_list, module_res, resource_module)
        resource_module.add_association_list(ass_list)
        source_hash_str = self._deps_hash_str(self.deps)
        tests_hash_str = ref_str(self._make_source_ref(self._tests))
        log.info("Write: %s: %s", self.name, self._resources_path)
        resource_module.save_as(self._resources_path, source_hash_str, tests_hash_str, ref_str(self._generator_ref))
        self._resource_module = resource_module
        self._ctx.resource_registry.set_module(self.name, resource_module)
        self._is_up_to_date = True
        await _lock_and_notify_all(self._unit_constructed)

    async def run(self, process_pool):
        log.info("Run: %s", self)
        if not self._resource_module.is_auto_generated:
            await self._set_service_providers(self._resource_module.provided_services)
            return
        info = _resource_module_info(self._resource_module, self.code_name)
        if self._deps_hash_str(self.deps) == self._resource_module.source_ref_str:
            await self._set_service_providers(self._resource_module.provided_services)
            self.deps.update(info.want_deps)
            log.info("%s: sources match", self.name)
            await self._wait_for_all_test_targets()
            if self._deps_hash_str(self._tests) == self._resource_module.tests_ref_str:
                self._is_up_to_date = True
                log.info("%s: tests match; up-to-date", self.name)
                return
            log.info("%s: tests do not match", self.name)
        else:
            log.info("%s: sources do not match", self.name)
        info, self._attr_list = await self._discover_attributes(process_pool)
        await self._set_service_providers(_enum_provided_services(self._attr_list))
        await self._wait_for_deps(self.deps)
        await self._call_all_fn_attrs(process_pool, self._attr_list)
        await self._wait_for_tests(self._tests)
        await self._construct()

    def add_test(self, test_unit):
        self._tests.add(test_unit)

    def add_used_types(self, used_types):
        self._used_types |= used_types


class FixturesDepsProviderUnit(Unit):

    def __init__(self, graph, ctx, generator_ref, root_dir, path):
        super().__init__(graph, ctx, generator_ref, root_dir, path)
        self._provided_deps = set()

    async def _set_service_providers(self, provide_services):
        self._provided_deps = {
            ServiceDep(service_name) for service_name in provide_services
            }

    @property
    def provided_deps(self):
        return self._provided_deps


class FixturesUnit(FixturesDepsProviderUnit):

    def __repr__(self):
        return f"<FixturesUnit {self.name!r}>"

    @property
    def is_fixtures(self):
        return True

    @cached_property
    def _target_unit_name(self):
        l = self._stem.split('.')
        assert l[-1] == 'fixtures'
        return self._dir + '.' + '.'.join(l[:-1])

    def init(self):
        super().init()
        dep = FixturesDep(self._target_unit_name)
        self._graph.dep_to_provider[dep] = self
        self._graph.name_to_deps[self._target_unit_name].add(dep)


class TestsUnit(FixturesDepsProviderUnit):

    def __init__(self, graph, ctx, generator_ref, root_dir, path):
        super().__init__(graph, ctx, generator_ref, root_dir, path)
        self._targets_discovered = False
        self._completed = False
        self._tested_units = None  # Unit list
        self._tested_services = None  # str set

    def __repr__(self):
        return f"<TestsUnit {self.name!r}>"

    @property
    def is_tests(self):
        return True

    def provided_dep_resource(self, dep):
        raise NotImplementedError()

    @property
    def targets_discovered(self):
        return self._targets_discovered

    @property
    def test_completed(self):
        return self._completed

    async def _imports_discovered(self, info):
        await super()._imports_discovered(info)
        self._tested_units = []
        for code_name in info.test_code:
            unit = self._graph.unit_by_code_name(code_name)
            unit.add_test(self)
            self._tested_units.append(unit)
        self._tested_services = info.test_services
        self._targets_discovered = True
        await _lock_and_notify_all(self._test_targets_discovered)

    async def _call_test(self, process_pool, attr_name, test_recorders, module_res, call_res, tested_service_to_unit):
        log.info("%s: Call test: %s", self.name, attr_name)
        unit_recorders, tested_unit_fields = tested_units(self._graph, self._ctx, self, module_res, self._tested_units)
        service_recorders, services_ass_list, tested_service_fields = tested_services(self._graph, self._ctx, self, module_res, tested_service_to_unit)
        recorders = {**test_recorders, **unit_recorders, **service_recorders}
        result = await process_pool.run(
            test_driver.call_test,
            import_recorders=_recorder_piece_list(recorders),
            module_res=module_res,
            test_call_res=call_res,
            tested_units=tested_unit_fields,
            tested_services=tested_service_fields,
            trace_modules=[],
            )
        await self._handle_result_imports(result.imports)

    async def _call_all_tests(self, process_pool):
        tested_service_to_unit = {}
        await self._wait_for_deps_discovered(self._tested_units)
        await self._wait_for_providers([ServiceDep(service_name) for service_name in self._tested_services])
        await self._wait_for_deps(self.deps | {dep for unit in self._tested_units for dep in unit.deps})
        for service_name in self._tested_services:
            provider = self._graph.dep_to_provider[ServiceDep(service_name)]
            if provider not in self._tested_units:
                raise RuntimeError(f"Service {service_name!r} provider {provider} does not belong to tested code modules: {self._tested_units}")
            tested_service_to_unit[service_name] = provider
        async with asyncio.TaskGroup() as tg:
            for attr in self._attr_list:
                if not isinstance(attr, htypes.inspect.fn_attr):
                    continue
                if not attr.name.startswith('test'):
                    continue
                recorders, module_res, call_res = test_call_res(self._graph, self._ctx, self, attr)
                tg.create_task(self._call_test(process_pool, attr.name, recorders, module_res, call_res, tested_service_to_unit))

    async def run(self, process_pool):
        log.info("Run: %s", self)
        if self._resource_module:
            info = _resource_module_info(self._resource_module, self.code_name)
            if self._deps_hash_str(self.deps | info.want_deps) == self._resource_module.source_ref_str:
                await self._set_service_providers(self._resource_module.provided_services)
                self.deps.update(info.want_deps)
                log.info("%s: sources match", self.name)
        info, self._attr_list = await self._discover_attributes(process_pool)
        await self._set_service_providers(_enum_provided_services(self._attr_list))
        await self._call_all_tests(process_pool)
        self._completed = True
        await _lock_and_notify_all(self._test_completed)
