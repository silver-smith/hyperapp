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
from .code.dep import CodeDep, FixturesDep, ServiceDep, ModuleDep
from .code import import_driver, call_driver, htest_driver
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
from .code.call_trace import CallTrace
from .code import ui_ctr

log = logging.getLogger(__name__)


class DeadlockError(RuntimeError):
    pass


ResModuleInfo = namedtuple('DesModuleInfo', 'use_modules want_deps test_code test_services')
ImportsInfo = namedtuple('ImportsInfo', 'used_types want_deps test_code test_services')


def _unit_list_to_str(unit_list):
    return ", ".join(unit.name for unit in unit_list)


def _flatten_set(set_list):
    result = set()
    for s in set_list:
        result |= s
    return result


def _sources_ref_str(units):
    deps = tuple(
        u.source_dep_record for u in
        sorted(units, key=attrgetter('name'))
        )
    sources_ref = mosaic.put(htypes.rc.module_deps(deps))
    return ref_str(sources_ref)


def _recorder_piece_list(recorders):
    piece_list = []
    for module_name, recorder_list in recorders.items():
        for rec in recorder_list:
            import_recorder = htypes.inspect.import_recorder(module_name, rec)
            piece_list.append(import_recorder)
    return tuple(piece_list)


def _module_import_list_to_dict(module_import_list):
    module_name_to_imports = defaultdict(set)
    for rec in module_import_list:
        module_name_to_imports[rec.module] |= set(rec.imports)
    return module_name_to_imports


def _resource_module_info(resource_module, code_module_name):
    use_modules = set()
    want_deps = set()
    test_code = set()
    test_services = set()
    for module_name, var_name in resource_module.used_imports:
        if module_name != 'builtins' and not module_name.startswith('legacy_type.'):
            want_deps.add(ModuleDep(module_name))
    import_list = resource_module.code_module_imports(code_module_name)
    for name, value in import_list.items():
        if value != 'phony':
            module_name, var_name = value.split(':')
            if module_name != 'builtins' and not module_name.startswith('legacy_type.'):
                use_modules.add(module_name)
        l = name.split('.')
        if len(l) == 2:
            what, name = l
            if what == 'code':
                want_deps.add(CodeDep(name))
            if what == 'services':
                want_deps.add(ServiceDep(name))
        if len(l) == 3:
            do, what, name = l
            if do != 'tested':
                continue
            if what == 'code':
                test_code.add(name)
            if what == 'services':
                test_services.add(name)
    return ResModuleInfo(
        use_modules=use_modules,
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
    _attributes_discovered = asyncio.Condition()
    _test_targets_discovered = asyncio.Condition()
    _test_completed = asyncio.Condition()
    _unit_up_to_date = asyncio.Condition()

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
        self._call_list = []  # CallTrace list
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
        log.debug("%s: manually created", self.name)
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
    def attributes_discovered(self):
        return self._attr_list is not None

    @property
    def deps(self):
        return self._graph.name_to_deps[self.name]

    @cached_property
    def source_dep_record(self):
        source_ref = mosaic.put(self._source_path.read_bytes())
        return htypes.rc.source_dep(self.name, source_ref)

    def _deps_sources(self, dep_set):
        unit_set = {self}
        for dep in dep_set:
            try:
                unit = self._graph.dep_to_provider[dep]
            except KeyError:
                raise RuntimeError(f"{self.name}: Attempt to hash deps to not-yet-discovered dep: {dep}")
            if unit.is_builtins:
                continue
            unit_set.add(unit)
        return unit_set

    @property
    def sources(self):
        return self._deps_sources(self.deps)

    @property
    def _test_sources(self):
        return _flatten_set(t.tested_sources for t in self._tests)

    @property
    def _test_sources_deps(self):
        return _flatten_set(t.tested_sources_deps for t in self._tests)

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

    def attr_constructors_associations(self, module_res):
        assert self._attr_list is not None  # Not yet imported/attr enumerated.
        name_to_res = {}  # Not used.
        ass_list = invite_attr_constructors(self._ctx, self._attr_list, module_res, name_to_res)
        return ass_list

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
                not_discovered = [
                    unit for unit in self._graph.name_to_unit.values()
                    if unit.is_tests and not unit.targets_discovered
                    ]
                if not not_discovered:
                    return
                log.debug("%s: Tests not yet discovered: %s", self.name, _unit_list_to_str(not_discovered))
                await self._test_targets_discovered.wait()

    async def _wait_for_providers(self, dep_set):
        async with self._providers_changed:
            while True:
                unknown = [repr(dep) for dep in dep_set if dep not in self._graph.dep_to_provider]
                if not unknown:
                    return
                log.debug("%s: Unknown providers for deps: %s", self.name, ", ".join(unknown))
                try:
                    await self._providers_changed.wait()
                except asyncio.CancelledError:
                    raise DeadlockError("Waiting providers for deps: {}".format(", ".join(unknown)))

    async def _wait_for_deps_discovered(self, units):
        async with self._new_deps_discovered:
            while True:
                not_discovered = {u for u in units if not u.deps_discovered}
                if not not_discovered:
                    return
                log.debug("%s: Deps not discovered: %s", self.name, _unit_list_to_str(not_discovered))
                try:
                    await self._new_deps_discovered.wait()
                except asyncio.CancelledError:
                    raise DeadlockError("Waiting for deps disccoverred: {}".format(_unit_list_to_str(not_discovered)))

    async def _wait_for_deps(self, dep_set):
        await self._wait_for_providers(dep_set)
        async with self._unit_up_to_date:
            while True:
                providers = {self._graph.dep_to_provider[dep] for dep in dep_set}
                outdated = [p for p in providers if not p.is_up_to_date]
                if not outdated:
                    return
                log.debug("%s: Outdated providers: %s", self.name, _unit_list_to_str(outdated))
                await self._unit_up_to_date.wait()

    async def _wait_for_tests(self, unit_list):
        async with self._test_completed:
            while True:
                not_completed = [u for u in unit_list if not u.test_completed]
                if not not_completed:
                    return
                log.debug("%s: Waiting for tests: %s", self.name, _unit_list_to_str(not_completed))
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
        self._handle_result_imports(result.imports)
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
            self._handle_result_imports(result.imports)
        attr_list = [web.summon(ref) for ref in result.attr_list]
        return info, attr_list

    def _fixtures_unit(self):
        return self._graph.dep_to_provider.get(FixturesDep(self.name))

    def _handle_result_imports(self, result_imports):
        imports_dict = _module_import_list_to_dict(result_imports)
        for name, imports in imports_dict.items():
            info = _imports_info(imports)
            unit = self._graph.name_to_unit[name]
            unit.add_used_types(info.used_types)
            log.debug("%s: discovered imports for %s: %s", self.name, name, info)

    def _handle_result_calls(self, call_list):
        name_to_calls = defaultdict(list)
        for call in call_list:
            trace = CallTrace.from_piece(call)
            name_to_calls[trace.module_name].append(trace)
        for name, calls in name_to_calls.items():
            unit = self._graph.name_to_unit[name]
            unit.add_calls(calls)

    async def _call_fn_attr(self, process_pool, attr_name, recorders, call_res):
        log.info("%s: Call attribute: %s", self.name, attr_name)
        result = await process_pool.run(
            call_driver.call_function,
            import_recorders=_recorder_piece_list(recorders),
            call_result_ref=mosaic.put(call_res),
            trace_modules=[self.name],
            )
        self._handle_result_imports(result.imports)
        self._handle_result_calls(result.calls)

    async def _call_all_fn_attrs(self, process_pool, attr_list):
        fixtures = self._fixtures_unit()
        async with asyncio.TaskGroup() as tg:
            for attr in attr_list:
                if not isinstance(attr, htypes.inspect.fn_attr):
                    continue
                if isinstance(attr, htypes.inspect.class_attr):
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
        ass_list += ui_ctr.create_ui_resources(self._ctx, self.name, resource_module, module_res, self._call_list)
        resource_module.add_association_list(ass_list)
        source_hash_str = _sources_ref_str(self.sources)
        tests_hash_str = _sources_ref_str(self._test_sources)
        log.info("Write: %s: %s", self.name, self._resources_path)
        resource_module.save_as(self._resources_path, source_hash_str, tests_hash_str, ref_str(self._generator_ref))
        self._resource_module = resource_module
        self._ctx.resource_registry.set_module(self.name, resource_module)
        self._is_up_to_date = True
        await _lock_and_notify_all(self._unit_up_to_date)

    async def _check_up_to_date(self):
        if self._resource_module and not self._resource_module.is_auto_generated:
            log.info("%s: manually created", self.name)
            self._graph.dep_to_provider[ModuleDep(self.name)] = self
            await self._set_service_providers(self._resource_module.provided_services)
            return True
        if not self._resource_module:
            log.info("%s: no resources yet", self.name)
            return False
        info = _resource_module_info(self._resource_module, self.code_name)
        await self._wait_for_providers(info.want_deps)
        # self.deps already contains fixtures deps.
        dep_sources = self._deps_sources(self.deps | info.want_deps)
        if _sources_ref_str(dep_sources) != self._resource_module.source_ref_str:
            log.info("%s: sources do not match", self.name)
            return False
        log.info("%s: sources match", self.name)
        self._graph.dep_to_provider[ModuleDep(self.name)] = self
        await self._set_service_providers(self._resource_module.provided_services)
        self.deps.update(info.want_deps)
        await self._wait_for_all_test_targets()
        await self._wait_for_providers(self._test_sources_deps)
        if _sources_ref_str(self._test_sources) != self._resource_module.tests_ref_str:
            log.info("%s: tests do not match", self.name)
            return False
        await self._wait_for_deps(self.deps)
        self._ctx.resource_registry.set_module(self.name, self._resource_module)
        for name in self._resource_module:
            self._resource_module[name]  # Load all definitions to name cache.
        self._deps_discovered = True
        self._is_up_to_date = True
        log.info("%s: tests match; up-to-date", self.name)
        await _lock_and_notify_all(self._new_deps_discovered)
        await _lock_and_notify_all(self._attributes_discovered)
        await _lock_and_notify_all(self._unit_up_to_date)
        return True

    async def run(self, process_pool):
        log.info("Run: %s", self.name)
        if await self._check_up_to_date():
            return
        info, self._attr_list = await self._discover_attributes(process_pool)
        await _lock_and_notify_all(self._attributes_discovered)
        self._graph.dep_to_provider[ModuleDep(self.name)] = self
        await self._set_service_providers(_enum_provided_services(self._attr_list))
        await self._wait_for_deps(self.deps)
        await self._call_all_fn_attrs(process_pool, self._attr_list)
        await self._wait_for_all_test_targets()
        await self._wait_for_tests(self._tests)

        await self._construct()

    def add_test(self, test_unit):
        self._tests.add(test_unit)

    def add_used_types(self, used_types):
        self._used_types |= used_types

    def add_calls(self, calls):
        self._call_list += calls


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
        self._tested_units = None  # Unit set
        self._tested_services = None  # str set

    def __repr__(self):
        return f"<TestsUnit {self.name!r}>"

    @property
    def is_tests(self):
        return True

    def provided_dep_resource(self, dep):
        raise NotImplementedError()

    @property
    def tested_sources_deps(self):
        return _flatten_set(
            [self.deps] + [unit.deps for unit in self._tested_units])

    @property
    def tested_sources(self):
        return _flatten_set(
            [self.sources] + [unit.sources for unit in self._tested_units])

    @property
    def targets_discovered(self):
        return self._targets_discovered

    @property
    def test_completed(self):
        return self._completed

    async def _imports_discovered(self, info):
        await super()._imports_discovered(info)
        self._tested_units = set()
        for code_name in info.test_code:
            unit = self._graph.unit_by_code_name(code_name)
            unit.add_test(self)
            self._tested_units.add(unit)
        self._tested_services = info.test_services
        self._targets_discovered = True
        log.info("%s: test targets discovered: %s", self.name, _unit_list_to_str(self._tested_units))
        await _lock_and_notify_all(self._test_targets_discovered)

    async def _wait_for_attributes_discovered(self, unit_list):
        async with self._attributes_discovered:
            while True:
                not_discovered = [u for u in unit_list if not u.attributes_discovered]
                if not not_discovered:
                    return
                log.debug("%s: Waiting for attributes discovered: %s", self.name, _unit_list_to_str(not_discovered))
                await self._attributes_discovered.wait()

    async def _call_test(self, process_pool, attr_name, test_recorders, module_res, call_res, tested_service_to_unit):
        log.info("%s: Call test: %s", self.name, attr_name)
        unit_recorders, ass_list, tested_unit_fields = tested_units(self._graph, self._ctx, self, module_res, self._tested_units)
        service_recorders, services_ass_list, tested_service_fields = tested_services(self._graph, self._ctx, self, module_res, tested_service_to_unit)
        recorders = {**test_recorders, **unit_recorders, **service_recorders}
        result = await process_pool.run(
            htest_driver.call_test,
            import_recorders=_recorder_piece_list(recorders),
            module_res=module_res,
            test_call_res=call_res,
            tested_units=tested_unit_fields,
            tested_services=tested_service_fields,
            trace_modules=[self.name] + [unit.name for unit in self._tested_units],
            use_associations=[ass.to_piece(mosaic) for ass in ass_list],
            )
        self._handle_result_imports(result.imports)
        self._handle_result_calls(result.calls)

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
        await self._wait_for_attributes_discovered([*tested_service_to_unit.values(), *self._tested_units])
        async with asyncio.TaskGroup() as tg:
            for attr in self._attr_list:
                if not isinstance(attr, htypes.inspect.fn_attr):
                    continue
                if not attr.name.startswith('test'):
                    continue
                recorders, module_res, call_res = test_call_res(self._graph, self._ctx, self, attr)
                tg.create_task(self._call_test(process_pool, attr.name, recorders, module_res, call_res, tested_service_to_unit))

    async def _construct(self):
        resource_module = resource_module_factory(self._ctx.resource_registry, self.name)
        phony_resource = htypes.phony.phony()
        tested_code_imports = [
            htypes.builtin.import_rec(f'tested.code.{unit.code_name}', mosaic.put(phony_resource))
            for unit in self._tested_units
            ]
        tested_services_imports = [
            htypes.builtin.import_rec(f'tested.services.{service_name}', mosaic.put(phony_resource))
            for service_name in self._tested_services
            ]
        module_res = self.make_module_res(sorted([
            *enum_dep_imports(self._graph, self.deps),
            *tested_code_imports,
            *tested_services_imports,
            ]))
        resource_module['phony'] = phony_resource
        resource_module[f'{self.code_name}.module'] = module_res
        source_hash_str = _sources_ref_str(self.sources)
        tests_hash_str = ''
        log.info("Write: %s: %s", self.name, self._resources_path)
        resource_module.save_as(self._resources_path, source_hash_str, tests_hash_str, ref_str(self._generator_ref))

    async def _check_up_to_date(self):
        if not self._resource_module:
            log.info("%s: no resources yet", self.name)
            return False
        info = _resource_module_info(self._resource_module, self.code_name)
        dep_sources = {self} | {self._graph.name_to_unit[module_name] for module_name in info.use_modules}
        if _sources_ref_str(dep_sources) != self._resource_module.source_ref_str:
            log.info("%s: sources do not match", self.name)
            return False
        log.info("%s: sources match", self.name)
        self._tested_units = set()
        for code_name in info.test_code:
            unit = self._graph.unit_by_code_name(code_name)
            self._tested_units.add(unit)
            unit.add_test(self)
        await self._set_service_providers(self._resource_module.provided_services)
        self.deps.update(info.want_deps)
        self._targets_discovered = True
        await _lock_and_notify_all(self._test_targets_discovered)
        await self._wait_for_deps_discovered(self._tested_units)
        outdated = {unit for unit in self._tested_units if not unit.is_up_to_date}
        if outdated:
            log.info("%s: outdated tested units: %s; up-to-date: %s",
                     self.name, ", ".join(u.name for u in outdated), ", ".join({u.name for u in self._tested_units - outdated}))
            return False
        log.info("%s: all tested units are up-to-date: %s", self.name, _unit_list_to_str(self._tested_units))
        self._is_up_to_date = True
        return True

    async def run(self, process_pool):
        log.info("Run: %s", self.name)
        if await self._check_up_to_date():
            return
        info, self._attr_list = await self._discover_attributes(process_pool)
        await self._set_service_providers(_enum_provided_services(self._attr_list))
        await self._call_all_tests(process_pool)
        await self._construct()
        self._completed = True
        self._is_up_to_date = True
        await _lock_and_notify_all(self._test_completed)
