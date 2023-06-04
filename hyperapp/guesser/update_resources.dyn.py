import enum
import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager
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
    legacy_service_resource_loader,
    legacy_type_resource_loader,
    local_types,
    module_dir_list,
    mosaic,
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

_log = logging.getLogger(__name__)


# These services are provided by resources now. Do not try to pick them from legacy services.
resource_services = [
    'endpoint_registry',
    'route_table',
    'rpc_call_factory',
    'rpc_endpoint_factory',
    'sync_route_table',
    'transport',
    ]

SourceInfo = namedtuple('SourceInfo', 'import_name attr_list provided_services used_types')
DepsInfo = namedtuple('DepsInfo', 'uses_modules wants_services wants_code tests_services tests_code')
ObjectInfo = namedtuple('ObjectInfo', 'dir get_result_t')


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
    def is_legacy_module(self):
        yaml_path = self.source_path.with_name(self.name + '.yaml')
        return yaml_path.exists()

    @cached_property
    def is_fixtures(self):
        return 'fixtures' in self.name.split('.')

    @cached_property
    def is_tests(self):
        return self.name.split('.')[-1] == 'tests'

    @property
    def up_to_date(self):
        if self.is_legacy_module:
            return True
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

    @cached_property
    def code_module_pair(self):
        if self.is_legacy_module:
            l = self.module_name.split('.')
            package = '.'.join(l[:-1])
            return (f'legacy_module.{package}', self.name)
        else:
            return (self.module_name, f'{self.name}.module')

    def _set_resource_module(self, resource_registry, resource_module):
        self.resource_module = resource_module
        resource_registry.set_module(self.module_name, self.resource_module)

    def init_resource_module(self, resource_registry, file_dict):
        if self.is_legacy_module:
            return
        if not self.resources_path.exists():
            self.is_manually_generated = False
            return
        resource_module = resource_module_factory(resource_registry, self.module_name, self.resources_path)
        self.is_manually_generated = not resource_module.is_auto_generated
        deps = self._get_resource_module_deps(resource_module)
        provides_services = resource_module.provided_services
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
        self.provides_services = provides_services
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
        return htypes.update_resources.source_dep(self.module_name, source_ref)

    # Returns None if provider deps for wanted services are not yet ready.
    def _collect_dep_modules(self, resource_registry, file_dict, deps):
        assert not self.is_legacy_module
        code_providers = code_provider_modules(file_dict)
        service_providers = service_provider_modules(file_dict, want_up_to_date=False)
        dep_list = []
        for code_name in deps.wants_code:
            try:
                provider = code_providers[code_name]
            except KeyError:
                raise RuntimeError(f"Module {self.module_name!r} wants code module {code_name!r}, but no one provides it")
            if provider.is_legacy_module:
                continue
            _log.info("%s wants code %r from: %s", self.module_name, code_name, provider.module_name)
            dep_list.append(provider)
        for service_name in deps.wants_services:
            try:
                provider = service_providers[service_name]
            except KeyError:
                # Resource services takes precedence over legacy ones.
                if is_legacy_service(resource_registry, service_name):
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
        return htypes.update_resources.module_deps(deps)

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
    def _discover_module_res(self, resource_registry, type_res_list, process):
        resource_list = [*type_res_list]

        resource_list += [
            htypes.import_recorder.resource(('services', 'mark'), mosaic.put(
                resource_registry['common.mark', 'mark.service'])),
            htypes.import_recorder.resource(('services', 'on_stop'), mosaic.put(
                resource_registry['legacy_service', 'on_stop'])),
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
        if self.is_legacy_module or self.up_to_date:
            return
        if not self.deps:
            _log.info("%s: Collect deps", self.module_name)
            import_recorder, import_discoverer, module_res = self._discover_module_res(
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
            module = resource_registry[provider.code_module_pair]
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

    def _visit_function(self, process, fixtures_file, object_res, ass_list, attr, path):
        attr_path = [*path, attr.name]
        attr_path_str = '.'.join(attr_path)
        attr_res = htypes.attribute.attribute(
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

        call_res = htypes.call.call(mosaic.put(function_res))

        _log.info("Retrieving type for: %s %s; %s", self.name, attr_path_str, call_res)
        get_resource_type = process.rpc_call(runner.get_resource_type)
        result_t = get_resource_type(resource_ref=mosaic.put(call_res), use_associations=ass_list)
        _log.info("Retrieved type for: %s %s: %r", self.name, attr_path_str, result_t)

        if isinstance(result_t, htypes.inspect.coroutine_t):
            async_run = htypes.async_run.async_run(mosaic.put(call_res))
            result_t = get_resource_type(resource_ref=mosaic.put(async_run), use_associations=ass_list)
            _log.info("Retrieved async call type for: %s %s: %r", self.name, attr_path_str, result_t)

        return (call_res, result_t)

    def _construct_dir(self, custom_types, resource_module, name):
        dir_name = camel_to_snake(f'{name}_d')
        dir_t_ref = custom_types[self.name][dir_name]
        dir_t = types.resolve(dir_t_ref)
        dir = dir_t()
        resource_module[dir_name] = dir
        return dir

    def _construct_method_command(self, custom_types, resource_module, object_name, object_dir, attr):
        dir = self._construct_dir(custom_types, resource_module, f'{object_name}_{attr.name}')

        command = htypes.impl.method_command_impl(
            method=attr.name,
            params=attr.param_list,
            dir=mosaic.put(dir),
            )
        resource_module[f'{object_name}.{attr.name}.command'] = command

        # Called for every command, but results with single resource.
        object_commands_d = htypes.command.object_commands_d()
        resource_module['object_commands_d'] = object_commands_d

        association = htypes.lcs.lcs_set_association(
            dir=(mosaic.put(object_dir), mosaic.put(object_commands_d)),
            value=mosaic.put(command),
            )
        resource_module.add_association(association)

    def _visit_object(self, process, custom_types, resource_module, fixtures_file, ass_list, object_name, object_res):
        _log.debug("Collect attributes for: %s.%s", self.module_name, object_name)
        collect_attributes = process.rpc_call(runner.collect_attributes)
        object_attrs = collect_attributes(object_ref=mosaic.put(object_res))

        attr_list = [web.summon(ref) for ref in object_attrs.attr_list]
        _log.info("Collected attrs for %s.%s: %s", self.module_name, object_name, attr_list)
        if 'get' not in [attr.name for attr in attr_list]:
            _log.info("Object %s.%s does not have 'get' method; skipping", self.module_name, object_name)
            return None

        object_dir = self._construct_dir(custom_types, resource_module, object_name)

        get_attr = next(attr for attr in attr_list if attr.name == 'get')
        if not isinstance(get_attr, htypes.inspect.fn_attr):
            raise RuntimeError(f"{self.name}: {object_name}.get should be a function")
        _, get_result_t = self._visit_function(process, fixtures_file, object_res, ass_list, get_attr, path=[object_name])

        for attr in attr_list:
            if attr.name == 'get':
                continue
            if not isinstance(attr, htypes.inspect.fn_attr):
                continue
            _, result_t = self._visit_function(process, fixtures_file, object_res, ass_list, attr, path=[object_name])
            self._construct_method_command(custom_types, resource_module, object_name, object_dir, attr)

        return ObjectInfo(object_dir, get_result_t)

    def _visit_attribute(self, process, custom_types, resource_module, fixtures_file, module_res, ass_list, attr):
        if not isinstance(attr, htypes.inspect.fn_attr):
            return None
        call_res, result_t = self._visit_function(process, fixtures_file, module_res, ass_list, attr, path=[])
        if list(attr.param_list) == ['piece'] and isinstance(result_t, htypes.inspect.object_t):
            return self._visit_object(process, custom_types, resource_module, fixtures_file, ass_list, attr.name, call_res)

    def _imports_to_type_set(self, import_set):
        used_types = set()
        for imp in import_set:
            if len(imp) < 3:
                continue
            kind, module, name = imp
            if kind != 'htypes':
                continue
            used_types.add((module, name))
        return used_types

    def _visit_module(self, process, resource_registry, custom_types, type_res_list, tested_module_imports, file_dict, resource_module, fixtures_file):
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

        object_info_dict = {}
        for attr in self.source_info.attr_list:
            object_info = self._visit_attribute(process, custom_types, resource_module, fixtures_file, module_res, ass_list, attr)
            if object_info:
                object_info_dict[attr.name] = object_info

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
                import_set = tested_module_imports.setdefault(module_name, set())
                import_set |= imports

        return (self.source_info.used_types | used_types, object_info_dict)

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

    def _construct_list_spec(self, custom_types, resource_module, object_name, object_info):
        key_attribute, key_t_name = pick_key_t(object_info.get_result_t, error_prefix=f"{self.name} {object_name}")
        key_t_ref = custom_types[key_t_name.module][key_t_name.name]
        key_t_res = htypes.builtin.legacy_type(key_t_ref)
        spec = htypes.impl.list_spec(
            key_attribute=key_attribute,
            key_t=mosaic.put(key_t_res),
            dir=mosaic.put(object_info.dir),
            )
        resource_module[f'{object_name}.spec'] = spec
        return spec

    # Assume that constructor attr.param_list == ['piece'] checked before.
    def _pick_and_check_piece_type(self, process, custom_types, fixtures_file, object_name):
        fixture = self._parameter_fixture(fixtures_file, [object_name, 'piece'])
        get_resource_type = process.rpc_call(runner.get_resource_type)
        piece_t = get_resource_type(resource_ref=mosaic.put(fixture), use_associations=[])
        _log.info("%s %s piece type: %r", self.name, object_name, piece_t)
        if not isinstance(piece_t, htypes.inspect.record_t):
            raise RuntimeError(
                f"{self.module_name}: {object_name} 'piece' parameter: Expected record type, but got: {piece_t!r}")
        piece_t_ref = custom_types[piece_t.type.module][piece_t.type.name]
        piece_t_res = htypes.builtin.legacy_type(piece_t_ref)
        return piece_t_res

    def _construct_object_impl(self, process, custom_types, resource_module, fixtures_file, module_res, object_name, object_info):
        if not isinstance(object_info.get_result_t, htypes.inspect.list_t):
            raise RuntimeError(
                f"{self.name}: Unsupported {object_name}.get method result type: {object_info.get_result_t!r}")
        piece_t_res = self._pick_and_check_piece_type(process, custom_types, fixtures_file, object_name)
        spec = self._construct_list_spec(custom_types, resource_module, object_name, object_info)

        ctr_attribute = htypes.attribute.attribute(
            object=mosaic.put(module_res),
            attr_name=object_name,
            )
        resource_module[object_name] = ctr_attribute

        impl_association = htypes.impl.impl_association(
            piece_t=mosaic.put(piece_t_res),
            ctr_fn=mosaic.put(ctr_attribute),
            spec=mosaic.put(spec),
            )
        resource_module.add_association(impl_association)

        pyobj_association = htypes.builtin.python_object_association(
            t=mosaic.put(piece_t_res),
            function=mosaic.put(ctr_attribute),
            )
        resource_module.add_association(pyobj_association)

    def call_attr_constructors(self, custom_types, resource_module, module_res):
        ass_list = []
        for attr in self.source_info.attr_list:
            for ctr_ref in attr.constructors:
                ass_list += constructor_creg.invite(ctr_ref, custom_types, resource_module, module_res, attr) or []
        return ass_list

    def construct_resources(self, process, resource_registry, custom_types, type_res_list, tested_module_imports, file_dict, saver):
        resource_module = resource_module_factory(resource_registry, self.name)
        fixtures_file = file_dict.get(f'{self.module_name}.fixtures')

        self._set_resource_module(resource_registry, resource_module)

        used_types, object_info_dict = self._visit_module(
            process, resource_registry, custom_types, type_res_list, tested_module_imports, file_dict, resource_module, fixtures_file)
        # Add types discovered by tests.
        used_types |= tested_module_imports.get(self.module_name, set())

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

        for name, object_info in object_info_dict.items():
            self._construct_object_impl(process, custom_types, resource_module, fixtures_file, module_res, name, object_info)
        ass_list = self.call_attr_constructors(custom_types, resource_module, module_res)
        for ass in ass_list:
            resource_module.add_association(ass)

        dep_modules = self._collect_dep_modules(resource_registry, file_dict, self.deps)
        module_deps_record = self._make_module_deps_record(dep_modules)
        source_ref = mosaic.put(module_deps_record)
        _log.info("Write %s: %s", self.name, self.resources_path)
        saver(resource_module, self.resources_path, ref_str(source_ref), ref_str(self._generator_ref))


process_code_module_list = [
    'common.lcs',
    'common.lcs_service',
    'ui.impl_registry',
    'ui.global_command_list',
    ]


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
        if (not file.is_legacy_module
            and file.provides_services is not None
            and (not want_up_to_date or file.up_to_date)
            and not file.is_fixtures
            and not file.is_tests
            )
        for service in file.provides_services
        }


def is_legacy_service(resource_registry, service_name):
    if service_name in resource_services:
        return False
    return ('legacy_service', service_name) in resource_registry


def service_resource(resource_registry, service_providers, service_name):
    try:
        provider = service_providers[service_name]
    except KeyError:
        try:
            return resource_registry['legacy_service', service_name]
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


def update_resources(generator_ref, subdir_list, root_dirs, module_list, rpc_timeout=10, process_name='update-resources-runner', saver=resource_saver):
    resource_dir_list = [hyperapp_dir / d for d in subdir_list] + root_dirs
    resource_registry = resource_registry_factory()

    custom_types, type_res_list = legacy_type_resources(resource_dir_list)
    legacy_type_modules = legacy_type_resource_loader(custom_types)
    add_legacy_types_to_cache(resource_registry, legacy_type_modules)
    resource_registry.update_modules(legacy_type_modules)

    resource_registry.set_module('legacy_service', legacy_service_resource_loader(resource_registry))

    tested_module_imports = {}  # module name -> type import tuple set

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
                    process, resource_registry, custom_types, type_res_list, tested_module_imports, file_dict, saver)
                idx += 1
            round += 1
