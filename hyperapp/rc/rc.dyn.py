import enum
import logging
import typing
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cached_property
from operator import attrgetter

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from hyperapp.common.htypes import HException, ref_str

from . import htypes
from .services import (
    builtin_types_as_dict,
    constructor_creg,
    endpoint_registry,
    hyperapp_dir,
    generate_rsa_identity,
    builtin_service_resource_loader,
    legacy_type_resource_loader,
    local_types,
    module_dir_list,
    mosaic,
    python_object_creg,
    resource_module_factory,
    resource_registry_factory,
    rpc_endpoint_factory,
    subprocess_rpc_server_running,
    type_module_loader,
    types,
    web,
    )
from .code.utils import camel_to_snake
from .code import runner
from .code import ui_ctl

_log = logging.getLogger(__name__)


SourceInfo = namedtuple('SourceInfo', 'import_name attr_list provided_services used_types')
DepsInfo = namedtuple('DepsInfo', 'uses_modules wants_services wants_code tests_services tests_code')


class TestResults:

    def __init__(self):
        self.type_import_set = set()
        self.call_list = []


@dataclass
class CallTrace:

    module_name: str
    line_no: int
    fn_qual_name: str
    obj_type: str
    params: dict

    @classmethod
    def from_piece(cls, piece):
        params = {
            p.name: web.summon(p.t)
            for p in piece.params
            }
        _log.info("Call trace: %s:%d: %s %s (%s)", piece.module, piece.line_no, piece.fn_qual_name, piece.obj_type or '-', params)
        return cls(piece.module, piece.line_no, piece.fn_qual_name, piece.obj_type, params)


@dataclass
class FunctionCallResult:

    t: typing.Any
    calls: list[CallTrace]

    @classmethod
    def from_piece(cls, piece):
        call_list = [CallTrace.from_piece(call) for call in piece.calls]
        return cls(web.summon(piece.t), call_list)


class ReadyStatus(enum.Enum):
    Ready = enum.auto()
    NotReady = enum.auto()
    ServicesNotReady = enum.auto()
    UpToDate = enum.auto()


def pick_key_t(result_t, error_prefix):
    name_to_type = {
        element.name: element.type
        for element in result_t.element_list
        }
    for name in ['id', 'key', 'idx', 'name']:
        try:
            return (name, name_to_type[name])
        except KeyError:
            pass
    raise RuntimeError(f"{error_prefix}: Unable to pick key element from: {list(name_to_type)}")


class SourceFile:

    def __init__(self, generator_ref, root_dir, source_path):
        self._generator_ref = generator_ref
        self.source_path = source_path
        self.name = source_path.name[:-len('.dyn.py')]
        self.module_name = str(source_path.relative_to(root_dir).with_name(self.name)).replace('/', '.')
        self.resources_path = source_path.with_name(self.name + '.resources.yaml')
        self.deps = None  # None if up_to_date.
        self.dep_modules = None  # None if up_to_date.
        self.provides_services = None
        self.tests_modules = None  # Only for tests.
        self._was_run = False  # Only for tests.
        self.source_info = None
        self.resource_module = None
        self.is_manually_generated = None

    def __repr__(self):
        return f"<SourceFile {self.module_name!r}>"

    @cached_property
    def is_fixtures(self):
        return 'fixtures' in self.name.split('.')

    @cached_property
    def is_tests(self):
        return self.name.split('.')[-1] == 'tests'

    @property
    def up_to_date(self):
        if self.is_tests:
            if self.tests_modules is None:
                return False
            if all(f.up_to_date for f in self.tests_modules):
                return True
            return self._was_run
        return self.resource_module is not None

    @property
    def ready_for_construction(self):
        return self.ready_status == ReadyStatus.Ready

    @property
    def ready_status(self):
        status = self.check_ready_status(skip_tests=False)
        if status != ReadyStatus.Ready:
            return status
        if self.is_tests:
            # Check all deps for tested modules are ready.
            if self.tests_modules is None:
                return ReadyStatus.ServicesNotReady
            for tested_module in self.tests_modules:
                # Tested module not ready if it tests are not ready, should skip tests check here.
                status = tested_module.check_ready_status(skip_tests=True)
                if status != ReadyStatus.Ready:
                    # Tested module deps are not yet ready.
                    return status
        return ReadyStatus.Ready

    def check_ready_status(self, skip_tests):
        if self.up_to_date:
            return ReadyStatus.UpToDate
        if self.dep_modules is None:
            return ReadyStatus.ServicesNotReady
        for f in self.dep_modules:
            if skip_tests and f.is_tests:
                continue
            if not f.up_to_date:
                return ReadyStatus.NotReady
        return ReadyStatus.Ready

    def _set_resource_module(self, resource_registry, resource_module):
        self.resource_module = resource_module
        resource_registry.set_module(self.module_name, self.resource_module)

    def init_resource_module(self, resource_registry, file_dict):
        if not self.resources_path.exists():
            self.is_manually_generated = False
            return
        resource_module = resource_module_factory(resource_registry, self.module_name, self.resources_path)
        deps = self._get_resource_module_deps(resource_module)
        self.is_manually_generated = not resource_module.is_auto_generated
        if self.is_manually_generated:
            _log.info("%s: manually generated", self.module_name)
        else:
            dep_modules = self._collect_dep_modules(resource_registry, file_dict, deps)
            if dep_modules is None:
                return  # Service provider deps are not yet ready.
            if not self._check_up_to_date(resource_module, dep_modules):
                return
            self.dep_modules = dep_modules
        self.deps = deps
        self.provides_services = resource_module.provided_services
        self._set_resource_module(resource_registry, resource_module)

    def _check_up_to_date(self, resource_module, dep_modules):
        if not resource_module.source_ref_str:
            _log.info("%s: no source ref", self.module_name)
            return False
        module_deps_record = self._make_module_deps_record(dep_modules)
        source_ref = mosaic.put(module_deps_record)
        if resource_module.source_ref_str != ref_str(source_ref):
            _log.info("%s: sources changed (%s)", self.module_name, [f.module_name for f in dep_modules])
            return False
        if not resource_module.generator_ref_str:
            _log.info("%s: no generator ref", self.module_name)
            return False
        if resource_module.generator_ref_str != ref_str(self._generator_ref):
            _log.info("%s: generator changed", self.module_name)
            return False
        _log.info("%s: up to date (%s)", self.module_name, [f.module_name for f in dep_modules])
        return True

    @cached_property
    def source_dep_record(self):
        source_ref = mosaic.put(self.source_path.read_bytes())
        return htypes.rc.source_dep(self.module_name, source_ref)

    # Returns None if provider deps for wanted services are not yet ready.
    def _collect_dep_modules(self, resource_registry, file_dict, deps):
        code_providers = code_provider_modules(file_dict)
        service_providers = service_provider_modules(file_dict, want_up_to_date=False)
        dep_list = []
        for code_name in deps.wants_code:
            try:
                provider = code_providers[code_name]
            except KeyError:
                raise RuntimeError(f"Module {self.module_name!r} wants code module {code_name!r}, but no one provides it")
            _log.info("%s wants code %r from: %s", self.module_name, code_name, provider.module_name)
            dep_list.append(provider)
        for service_name in deps.wants_services:
            try:
                provider = service_providers[service_name]
            except KeyError:
                if is_builtin_service(resource_registry, service_name):
                    continue
                _log.info("%s: provider deps for service %r is not yet ready", self.module_name, service_name)
                return None
            _log.info("%s wants service %r from: %s", self.module_name, service_name, provider.module_name)
            dep_list.append(provider)
        prefix = self.module_name.split('.')
        for file in file_dict.values():
            name_l = file.module_name.split('.')
            if name_l[:len(prefix)] != prefix:
                continue
            if len(name_l) != len(prefix) + 1:
                continue
            # Fixture, tests or aux file dep.
            _log.info("%s wants fixtures, tests or aux resources from: %s", self.module_name, file.module_name)
            dep_list.append(file)
        return dep_list

    def _make_module_deps_record(self, dep_modules):
        deps = [
            f.source_dep_record for f in
            sorted([self, *dep_modules], key=attrgetter('module_name'))
            ]
        return htypes.rc.module_deps(deps)

    @staticmethod
    def _get_resource_module_deps(resource_module):
        uses_modules = set()
        wants_services = set()
        wants_code = set()
        for module_name, var_name in resource_module.used_imports:
            uses_modules.add(module_name)
            l = var_name.split('.')
            if len(l) == 2 and l[1] == 'service':
                wants_services.add(l[0])
            if len(l) > 1 and l[-1] == 'module':
                wants_code.add('.'.join(l[:-1]))
        return DepsInfo(
            uses_modules=uses_modules,
            wants_services=wants_services,
            wants_code=wants_code,
            tests_services=set(),
            tests_code=set(),
            )

    def _make_module_res(self, import_list):
        return htypes.builtin.python_module(
            module_name=self.name,
            source=self.source_path.read_text(),
            file_path=str(self.source_path),
            import_list=tuple(import_list),
            )

    def _prepare_import_recorder(self, process, resource_list):
        import_recorder_res = htypes.import_recorder.import_recorder(resource_list)
        import_recorder_ref = mosaic.put(import_recorder_res)
        import_recorder = process.proxy(import_recorder_ref)
        import_recorder.reset()
        return (import_recorder, import_recorder_ref)

    def _prepare_import_discoverer(self, process):
        import_discoverer_res = htypes.import_discoverer.import_discoverer()
        import_discoverer_ref = mosaic.put(import_discoverer_res)
        import_discoverer = process.proxy(import_discoverer_ref)
        import_discoverer.reset()
        return (import_discoverer, import_discoverer_ref)

    # Module resource with import discoverer.
    def _discoverer_module_res(self, resource_registry, type_res_list, process):
        resource_list = [*type_res_list]

        resource_list += [
            htypes.import_recorder.resource(('services', 'mark'), mosaic.put(
                resource_registry['common.mark', 'mark.service'])),
            htypes.import_recorder.resource(('services', 'on_stop'), mosaic.put(
                resource_registry['builtin_service', 'on_stop'])),
            ]

        import_recorder, import_recorder_ref = self._prepare_import_recorder(process, resource_list)
        import_discoverer, import_discoverer_ref = self._prepare_import_discoverer(process)

        module_res = self._make_module_res([
                htypes.builtin.import_rec('htypes.*', import_recorder_ref),
                htypes.builtin.import_rec('services.*', import_recorder_ref),
                htypes.builtin.import_rec('*', import_discoverer_ref),
                ])
        return (import_recorder, import_discoverer, module_res)

    # Module resource with import recorder for htypes.
    def type_recorder_module_res(self, resource_registry, type_res_list, process, file_dict, service_providers):
        import_recorder, import_recorder_ref = self._prepare_import_recorder(process, type_res_list)
        module_res = self._make_module_res([
            *self._make_import_list(resource_registry, file_dict, service_providers),
            htypes.builtin.import_rec('htypes.*', import_recorder_ref),
            ])
        return (import_recorder, module_res)

    def _imports_to_deps(self, import_set):
        wants_services = set()
        wants_code = set()
        tests_services = set()
        tests_code = set()
        for imp in import_set:
            if imp[-1] == 'shape':
                imp = imp[:-1]  # Revert pycharm debugger mangle.
            if len(imp) < 2:
                continue
            kind, name, *_ = imp
            if kind == 'services':
                wants_services.add(name)
                continue
            if kind == 'code':
                wants_code.add(name)
                continue
            if kind == 'tested':
                if len(imp) < 3:
                    continue
                _, kind, name, *_ = imp
                if kind == 'services':
                    tests_services.add(name)
                    continue
                if kind == 'code':
                    tests_code.add(name)
                    continue
            if kind == 'htypes':
                continue  # TODO: store htypes used by top-level statements too.
            _log.warning("Unknown import kind (old-style import?): %r at %s", kind, self.source_path)
        _log.info("Discovered import deps: wants_services: %s", wants_services)
        _log.info("Discovered import deps: wants_code: %s", wants_code)
        _log.info("Discovered import deps: tests_services: %s", tests_services)
        _log.info("Discovered import deps: tests_code: %s", tests_code)

        return DepsInfo(
            uses_modules=set(),
            wants_services=wants_services,
            wants_code=wants_code,
            tests_services=tests_services,
            tests_code=tests_code,
            )

    def parse_source(self, import_recorder, import_discoverer, module_res, process, fail_on_incomplete):
        _log.debug("Collect attributes for: %r", self.module_name)
        collect_attributes = process.rpc_call(runner.collect_attributes)
        try:
            object_attrs = collect_attributes(object_ref=mosaic.put(module_res))
        except HException as x:
            if isinstance(x, htypes.import_discoverer.using_incomplete_object):
                if fail_on_incomplete:
                    raise RuntimeError(f"While constructing {self.module_name}: Using incomplete object: {x.message}")
                _log.warning("%s: Using incomplete object: %s", self.name, x.message)
                object_attrs = None
            else:
                raise
        else:
            attr_list = [web.summon(ref) for ref in object_attrs.attr_list]
            _log.info("Collected attrs for %r, module %s: %s", self.module_name, object_attrs.object_module, attr_list)

        used_imports = import_recorder.used_imports()
        _log.info("%s: used import list: %s", self.module_name, used_imports)
        import_set = set(used_imports)
        if import_discoverer:
            discovered_imports = import_discoverer.discovered_imports()
            _log.info("%s: discovered import list: %s", self.module_name, discovered_imports)
            import_set |= set(discovered_imports)

        if object_attrs:
            provided_services = set()
            for attr in attr_list:
                for ctr_ref in attr.constructors:
                    ctr = web.summon(ctr_ref)
                    if isinstance(ctr, htypes.attr_constructors.service):
                        provided_services.add(ctr.name)
                        _log.info("Discovered provided service: %r", ctr.name)
            source_info = SourceInfo(
                import_name=object_attrs.object_module,
                attr_list=attr_list,
                provided_services=provided_services,
                used_types=self._imports_to_type_set(import_set),
                )
        else:
            _log.info("Failed to load source info")
            source_info = None

        deps_info = self._imports_to_deps(import_set)
        return (deps_info, source_info)

    def init_deps(self, resource_registry, process, type_res_list, file_dict):
        if self.up_to_date:
            return
        if not self.deps:
            _log.info("%s: Collect deps", self.module_name)
            import_recorder, import_discoverer, module_res = self._discoverer_module_res(
                resource_registry, type_res_list, process)
            self.deps, self.source_info = self.parse_source(
                import_recorder, import_discoverer, module_res, process, fail_on_incomplete=False)
        if self.dep_modules is None:
            # Recheck service providers, deps for some may become ready.
            self.dep_modules = self._collect_dep_modules(resource_registry, file_dict, self.deps)
            # Now as service providers are ready, we can init resource module if it is up-to-date.
            self.init_resource_module(resource_registry, file_dict)
        if (self.provides_services is None
            and self.dep_modules is not None
            and all(f.up_to_date for f in self.dep_modules if not f.is_tests)
            ):
            _log.info("%s: Collect provides_services", self.module_name)
            service_providers = service_provider_modules(file_dict)
            if not self.source_info:
                import_recorder, module_res = self.type_recorder_module_res(
                    resource_registry, type_res_list, process, file_dict, service_providers)
                invalid_deps, self.source_info = self.parse_source(
                    import_recorder, None, module_res, process, fail_on_incomplete=True)
                # deps are invalid due to type_recorder_module_res usage.
            self.provides_services = self.source_info.provided_services
        if self.is_tests and self.tests_modules is None:
            code_providers = code_provider_modules(file_dict)
            service_providers = service_provider_modules(file_dict, want_up_to_date=False)
            tests_modules = {
                code_providers[name]
                for name in self.deps.tests_code
                }
            for service_name in self.deps.tests_services:
                try:
                    tests_modules.add(service_providers[service_name])
                except KeyError:
                    return  #  Provider module deps are not yet ready?
            self.tests_modules = tests_modules

    @staticmethod
    def module_service_provider_modules(file):
        return {
            service: file
            for service in file.provides_services
            }

    def _make_import_list(self, resource_registry, file_dict, service_providers):
        code_providers = code_provider_modules(file_dict)

        import_list = []

        for name in self.deps.wants_code:
            provider = code_providers[name]
            module = resource_registry[provider.module_name, f'{provider.name}.module']
            import_list.append(
                htypes.builtin.import_rec(f'code.{name}', mosaic.put(module)))

        for service_name in self.deps.wants_services:
            service = service_resource(resource_registry, service_providers, service_name)
            if service is None:
                raise RuntimeError(f"Provider deps for service {service_name!r} is not yet ready")
            import_list.append(
                htypes.builtin.import_rec(f'services.{service_name}', mosaic.put(service)))

        _log.info("Import list: %s", import_list)
        return import_list

    # def make_tested_module_res(self, resource_registry, type_res_list, process, file_dict, service_providers):
    #     fixtures_file = file_dict.get(f'{self.module_name}.fixtures')
    #     if fixtures_file:
    #         fixed_service_providers = {
    #             **service_providers,
    #             **self.module_service_provider_modules(fixtures_file),
    #             }
    #     else:
    #         fixed_service_providers = service_providers
    #     import_recorder, module_res = self.type_recorder_module_res(
    #         resource_registry, type_res_list, process, file_dict, fixed_service_providers)
    #     return (import_recorder, module_res)

    def _make_tested_import_list(self, resource_registry, custom_types, type_res_list, process, file_dict, service_providers):
        code_providers = code_provider_modules(file_dict)
        unready_service_providers = service_provider_modules(file_dict, want_up_to_date=False)
        # fixed_service_providers = {**service_providers, **self.module_service_provider_modules(self)}
        name_to_recorder = {}

        def type_recorder_module_res(provider):
            import_recorder, module_res = provider.type_recorder_module_res(
                resource_registry, type_res_list, process, file_dict, service_providers)
            name_to_recorder[provider.module_name] = import_recorder
            return module_res

        import_list = []
        for name in self.deps.tests_code:
            provider = code_providers[name]
            module_res = type_recorder_module_res(provider)
            import_list.append(
                htypes.builtin.import_rec(f'tested.code.{name}', mosaic.put(module_res)))

        ass_list = []
        for service_name in self.deps.tests_services:
            provider = unready_service_providers[service_name]
            module_res = type_recorder_module_res(provider)
            name_to_res = {}
            ass_list += provider.call_attr_constructors(custom_types, name_to_res, module_res)
            for name, resource in name_to_res.items():
                if name.endswith('.service'):
                    sn, _ = name.rsplit('.', 1)
                    if sn == service_name:
                        break
            else:
                raise RuntimeError(f"{provider.module_name}: Service {service_name!r} was not created by it's constructor")
            import_list.append(
                htypes.builtin.import_rec(f'tested.services.{service_name}', mosaic.put(resource)))

        return (name_to_recorder, import_list, ass_list)

    @staticmethod
    def _parameter_fixture(fixtures_file, path):
        if not fixtures_file:
            return None
        name = '.'.join([*path, 'parameter'])
        try:
            return fixtures_file.resource_module[name]
        except KeyError:
            return None

    def _visit_function(self, process, fixtures_file, object_res, tested_modules, ass_list, attr, path):
        attr_path = [*path, attr.name]
        attr_path_str = '.'.join(attr_path)
        attr_res = htypes.builtin.attribute(
            object=mosaic.put(object_res),
            attr_name=attr.name,
            )
        if attr.param_list:
            kw = {
                param: self._parameter_fixture(fixtures_file, [*attr_path, param])
                for param in attr.param_list
                }
            kw = {key: value for key, value in kw.items() if value is not None}
            _log.info("%s %s: Parameter fixtures: %s", self.name, attr_path_str, kw)
            missing_params = ", ".join(sorted(set(attr.param_list) - set(kw)))
            if missing_params:
                if kw:
                    raise RuntimeError(f"Some parameter fixtures are missing for {self.name} {attr_path_str}: {missing_params}")
                else:
                    # All are missing - guess this function is not intended to be tested using fixture parameters.
                    _log.warning("Parameter fixtures are missing for %s %s: %s", self.name, attr_path_str, missing_params)
                    return (None, None)
            function_res = htypes.partial.partial(
                function=mosaic.put(attr_res),
                params=[
                    htypes.partial.param(name, mosaic.put(value))
                    for name, value in kw.items()
                    ],
                )
        else:
            function_res = attr_res

        call_res = htypes.builtin.call(mosaic.put(function_res))

        _log.info("Retrieving type for: %s %s; %s", self.name, attr_path_str, call_res)
        get_resource_type = process.rpc_call(runner.get_resource_type)
        object_type_info = get_resource_type(
            resource_ref=mosaic.put(call_res),
            use_associations=[ass.to_piece(mosaic, python_object_creg) for ass in ass_list],
            tested_modules=tested_modules,
            )
        call_result = FunctionCallResult.from_piece(object_type_info)
        _log.info("Retrieved type for: %s %s: %s; calls=%r", self.name, attr_path_str, call_result.t, call_result.calls)
        return (call_res, call_result)

    def _visit_object(self, process, custom_types, resource_module, fixtures_file, ass_list, object_name, object_res):
        _log.debug("Collect attributes for: %s.%s", self.module_name, object_name)
        collect_attributes = process.rpc_call(runner.collect_attributes)
        object_attrs = collect_attributes(object_ref=mosaic.put(object_res))

        attr_list = [web.summon(ref) for ref in object_attrs.attr_list]
        _log.info("Collected attrs for %s.%s: %s", self.module_name, object_name, attr_list)
        if 'get' not in [attr.name for attr in attr_list]:
            _log.info("Object %s.%s does not have 'get' method; skipping", self.module_name, object_name)
            return None

        get_attr = next(attr for attr in attr_list if attr.name == 'get')
        if not isinstance(get_attr, htypes.inspect.fn_attr):
            raise RuntimeError(f"{self.name}: {object_name}.get should be a function")
        _ = self._visit_function(process, fixtures_file, object_res, [], ass_list, get_attr, path=[object_name])

        for attr in attr_list:
            if attr.name == 'get':
                continue
            if not isinstance(attr, htypes.inspect.fn_attr):
                continue
            _ = self._visit_function(process, fixtures_file, object_res, [], ass_list, attr, path=[object_name])

    def _visit_attribute(self, process, custom_types, resource_module, fixtures_file, module_res, tested_modules, ass_list, attr):
        if not isinstance(attr, htypes.inspect.fn_attr):
            return None
        call_res, call_result = self._visit_function(process, fixtures_file, module_res, tested_modules, ass_list, attr, path=[])
        if list(attr.param_list) == ['piece'] and call_result and isinstance(call_result.t, htypes.inspect.object_t):
            self._visit_object(process, custom_types, resource_module, fixtures_file, ass_list, attr.name, call_res)
        return call_result.calls if call_result else []

    def _imports_to_type_set(self, import_set):
        used_types = set()
        for imp in import_set:
            if len(imp) < 3:
                continue
            kind, module, name, *_ = imp
            if kind != 'htypes':
                continue
            used_types.add((module, name))
        return used_types

    def _visit_module(self, process, resource_registry, custom_types, type_res_list, test_results, file_dict, resource_module, fixtures_file):
        _log.info("%s: Discover type imports", self.module_name)

        service_providers = service_provider_modules(file_dict)
        if fixtures_file:
            service_providers.update(self.module_service_provider_modules(fixtures_file))

        if not self.source_info:
            import_recorder, collect_module_res = self.type_recorder_module_res(
                resource_registry, type_res_list, process, file_dict, service_providers)
            invalid_deps, self.source_info = self.parse_source(
                import_recorder, None, collect_module_res, process, fail_on_incomplete=True)

        import_list = self._make_import_list(resource_registry, file_dict, service_providers)

        import_recorder, import_recorder_ref = self._prepare_import_recorder(process, type_res_list)
        name_to_recorder, tested_import_list, ass_list = self._make_tested_import_list(
            resource_registry, custom_types, type_res_list, process, file_dict, service_providers)

        recorder_import_list = [
            *import_list,
            htypes.builtin.import_rec('htypes.*', import_recorder_ref),
            ]
        module_res = self._make_module_res([*tested_import_list, *recorder_import_list])

        call_list = []
        for attr in self.source_info.attr_list:
            calls = self._visit_attribute(
                process, custom_types, resource_module, fixtures_file, module_res, list(name_to_recorder), ass_list, attr)
            call_list += calls

        used_imports = import_recorder.used_imports()
        _log.info("Used import list: %s", used_imports)

        used_types = self._imports_to_type_set(used_imports)
        _log.info("Discovered import htypes: %s", used_types)

        name_to_imports = {
            module_name: self._imports_to_type_set(recorder.used_imports())
            for module_name, recorder in name_to_recorder.items()
            }
        if name_to_imports:
            _log.info("Discovered tested imports: %s", name_to_imports)
            for module_name, imports in name_to_imports.items():
                test_results[module_name].type_import_set.update(imports)

        if self.is_tests:
            for call in call_list:
                test_results[call.module_name].call_list.append(call)

        return self.source_info.used_types | used_types

    @staticmethod
    def _types_import_list(type_res_list, used_types):
        pair_to_resource_ref = {
            (r.name[1], r.name[2]): r.resource
            for r in type_res_list
            }
        return {
            htypes.builtin.import_rec(f'htypes.{pair[0]}.{pair[1]}', pair_to_resource_ref[pair])
            for pair in used_types
            }

    def call_attr_constructors(self, custom_types, resource_module, module_res):
        ass_list = []
        for attr in self.source_info.attr_list:
            for ctr_ref in attr.constructors:
                ass_list += constructor_creg.invite(ctr_ref, custom_types, resource_module, module_res, attr) or []
        return ass_list

    def construct_resources(self, process, resource_registry, custom_types, type_res_list, test_results, file_dict, saver):
        resource_module = resource_module_factory(resource_registry, self.name)
        fixtures_file = file_dict.get(f'{self.module_name}.fixtures')

        self._set_resource_module(resource_registry, resource_module)

        used_types = self._visit_module(
            process, resource_registry, custom_types, type_res_list, test_results, file_dict, resource_module, fixtures_file)
        # Add types discovered by tests.
        used_types |= test_results[self.module_name].type_import_set
        call_list = test_results[self.module_name].call_list

        if self.is_tests:
            self._was_run = True
            return  # Tests should not produce resources.

        service_providers = service_provider_modules(file_dict)
        import_list = [
            *self._make_import_list(resource_registry, file_dict, service_providers),
            *self._types_import_list(type_res_list, used_types),
            ]

        module_res = self._make_module_res(sorted(import_list))
        resource_module[f'{self.name}.module'] = module_res

        ass_list = ui_ctl.create_ui_resources(custom_types, self.module_name, resource_module, module_res, call_list)

        ass_list += self.call_attr_constructors(custom_types, resource_module, module_res)
        for ass in ass_list:
            resource_module.add_association(ass)

        dep_modules = self._collect_dep_modules(resource_registry, file_dict, self.deps)
        module_deps_record = self._make_module_deps_record(dep_modules)
        source_ref = mosaic.put(module_deps_record)
        _log.info("Write %s: %s", self.name, self.resources_path)
        saver(resource_module, self.resources_path, ref_str(source_ref), ref_str(self._generator_ref))


@contextmanager
def subprocess(process_name, additional_dir_list, rpc_timeout):
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_rpc_server_running(
            process_name,
            rpc_endpoint,
            identity,
            timeout_sec=rpc_timeout,
        ) as process:
        yield process


def legacy_type_resources(dir_list):
    custom_types = {
        **builtin_types_as_dict(),
        **local_types,
        }

    type_module_loader.load_type_modules(dir_list, custom_types)

    resource_list = []
    for module_name, type_module in custom_types.items():
        for name, type_ref in type_module.items():
            resource = htypes.builtin.legacy_type(type_ref)
            resource_ref = mosaic.put(resource)
            resource_list.append(
                htypes.import_recorder.resource(('htypes', module_name, name), resource_ref))
    return (custom_types, resource_list)


def add_legacy_types_to_cache(resource_registry, legacy_type_modules):
    for module_name, module in legacy_type_modules.items():
        for var_name in module:
            resource_registry.add_to_cache((module_name, var_name), module[var_name])


def code_provider_modules(file_dict):
    return {
        file.name: file
        for file in file_dict.values()
        }


def service_provider_modules(file_dict, want_up_to_date=True):
    return {
        service: file
        for module_name, file in file_dict.items()
        if (file.provides_services is not None
            and (not want_up_to_date or file.up_to_date)
            and not file.is_fixtures
            and not file.is_tests
            )
        for service in file.provides_services
        }


def is_builtin_service(resource_registry, service_name):
    return ('builtin_service', service_name) in resource_registry


def service_resource(resource_registry, service_providers, service_name):
    try:
        provider = service_providers[service_name]
    except KeyError:
        try:
            return resource_registry['builtin_service', service_name]
        except KeyError:
            return None  # Provider module deps are not yet ready?
    else:
        return resource_registry[provider.module_name, f'{service_name}.service']


def collect_source_files(generator_ref, subdir_list, root_dirs, resource_registry):
    file_dict = {}

    def add_source_files(root, dir):
        for path in dir.rglob('*.dyn.py'):
            if 'test' in path.relative_to(root).parts:
                continue
            file = SourceFile(generator_ref, root, path)
            file_dict[file.module_name] = file

    for subdir in subdir_list:
        add_source_files(hyperapp_dir, hyperapp_dir / subdir)
    for root in root_dirs:
        add_source_files(root, root)
    for file in file_dict.values():
        file.init_resource_module(resource_registry, file_dict)
    return file_dict


def init_deps(resource_registry, process, type_res_list, file_dict):
    for file in file_dict.values():
        file.init_deps(resource_registry, process, type_res_list, file_dict)


def resource_saver(resource_module, path, source_ref_str, generator_ref_str):
    resource_module.save_as(path, source_ref_str, generator_ref_str)


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, rpc_timeout=10, process_name='rc-runner', saver=resource_saver):
    _log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    resource_dir_list = [hyperapp_dir / d for d in subdir_list] + root_dirs
    resource_registry = resource_registry_factory()

    custom_types, type_res_list = legacy_type_resources(resource_dir_list)
    legacy_type_modules = legacy_type_resource_loader(custom_types)
    add_legacy_types_to_cache(resource_registry, legacy_type_modules)
    resource_registry.update_modules(legacy_type_modules)

    resource_registry.set_module('builtin_service', builtin_service_resource_loader(resource_registry))

    test_results = defaultdict(TestResults)  # module name -> TestResults

    with subprocess(process_name, resource_dir_list, rpc_timeout) as process:

        file_dict = collect_source_files(generator_ref, subdir_list, root_dirs, resource_registry)

        round = 0
        idx = 0
        while True:
            _log.info("****** Round #%d  %s", round, '*'*50)
            init_deps(resource_registry, process, type_res_list, file_dict)
            ready_files = sorted([f for f in file_dict.values() if f.ready_for_construction], key=attrgetter('module_name'))
            waits_services = [f for f in file_dict.values() if f.ready_status == ReadyStatus.ServicesNotReady]
            _log.info("Ready for construction: %s", ", ".join(f.module_name for f in ready_files))
            _log.info("Waits services: %s", ", ".join(f.module_name for f in waits_services))
            if not ready_files and waits_services:
                round += 1
                continue
            if module_list:
                wanted_files = [f for f in ready_files if f.module_name in module_list]
            else:
                wanted_files = ready_files
            if not wanted_files:
                if round == 0:
                    if module_list:
                        raise RuntimeError(f"No ready files among selected modules: {', '.join(module_list)}")
                    else:
                        _log.info("All files are up-to-date, nothing to do")
                        break
                _log.info("All %d files are constructed in %d rounds", idx, round)
                break
            for file in ready_files:
                if module_list and file.module_name not in module_list:
                    continue
                _log.info("****** #%d Construct resources for: %s  %s", idx, file.module_name, '*'*50)
                file.construct_resources(
                    process, resource_registry, custom_types, type_res_list, test_results, file_dict, saver)
                idx += 1
            round += 1
