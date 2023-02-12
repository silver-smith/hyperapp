import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from functools import cached_property
from operator import attrgetter

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from hyperapp.common.htypes import HException
from hyperapp.common.ref import hash_sha512

from . import htypes
from .services import (
    builtin_types_as_dict,
    code_module_loader,
    collect_attributes_ref,
    constructor_creg,
    endpoint_registry,
    hyperapp_dir,
    generate_rsa_identity,
    get_resource_type_ref,
    legacy_module_resource_loader,
    legacy_service_resource_loader,
    legacy_type_resource_loader,
    local_modules,
    local_types,
    module_dir_list,
    mosaic,
    resource_module_factory,
    resource_registry_factory,
    rpc_endpoint_factory,
    subprocess_running,
    type_module_loader,
    types,
    web,
    )
from .code.utils import camel_to_snake

_log = logging.getLogger(__name__)


SourceInfo = namedtuple('SourceInfo', 'import_name attr_list')
DepsInfo = namedtuple('DepsInfo', 'provides_services uses_modules wants_services wants_code tests_services tests_code')
ObjectInfo = namedtuple('ObjectInfo', 'dir get_result_t')


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
        self.deps = None
        self.source_info = None
        self.resource_module = None
        self.is_manually_generated = None

    def __repr__(self):
        return f"<SourceFile {self.module_name!r}>"

    @property
    def up_to_date(self):
        if self.is_legacy_module:
            return True
        return self.resource_module is not None

    @cached_property
    def is_legacy_module(self):
        yaml_path = self.source_path.with_name(self.name + '.yaml')
        return yaml_path.exists()

    @cached_property
    def code_module_pair(self):
        if self.is_legacy_module:
            l = self.module_name.split('.')
            package = '.'.join(l[:-1])
            return (f'legacy_module.{package}', self.name)
        else:
            return (self.module_name, f'{self.name}.module')

    def set_resource_module(self, resource_registry, resource_module):
        self.resource_module = resource_module
        self.deps = self.get_resource_module_deps()
        resource_registry.set_module(self.module_name, self.resource_module)

    def init_resource_module(self, resource_registry):
        if self.is_legacy_module:
            return
        if not self.resources_path.exists():
            self.is_manually_generated = False
            return
        resource_module = resource_module_factory(resource_registry, self.module_name, self.resources_path)
        self.is_manually_generated = not resource_module.is_auto_generated
        if self.is_manually_generated:
            _log.info("%s: manually generated", self.module_name)
        elif not self.check_up_to_date(resource_module):
            return
        self.set_resource_module(resource_registry, resource_module)

    def invalidate_resource_module(self, resource_registry):
        if self.is_legacy_module or self.is_manually_generated:
            return
        self.resource_module = None
        self.deps = None
        resource_registry.remove_module(self.module_name)

    def check_up_to_date(self, resource_module):
        if not resource_module.source_hash:
            _log.info("%s: no source hash", self.module_name)
            return False
        source_hash = hash_sha512(self.source_path.read_bytes())
        if resource_module.source_hash != source_hash:
            _log.info("%s: changed", self.module_name)
            return False
        if not resource_module.generator_hash:
            _log.info("%s: no generator hash", self.module_name)
            return False
        if resource_module.generator_hash != self._generator_ref.hash:
            _log.info("%s: generator changed", self.module_name)
            return False
        _log.info("%s: up to date", self.module_name)
        return True

    def get_resource_module_deps(self):
        uses_modules = set()
        wants_services = set()
        wants_code = set()
        for module_name, var_name in self.resource_module.used_imports:
            uses_modules.add(module_name)
            l = var_name.split('.')
            if len(l) == 2 and l[1] == 'service':
                wants_services.add(l[0])
            if len(l) > 1 and l[-1] == 'module':
                wants_code.add('.'.join(l[:-1]))
        return DepsInfo(
            provides_services=self.resource_module.provided_services,
            uses_modules=uses_modules,
            wants_services=wants_services,
            wants_code=wants_code,
            tests_services=set(),
            tests_code=set(),
            )

    # Can we load this resource module? Can we use it's code_module_pair?
    def deps_up_to_date(self, file_dict, name_to_file):
        if self.is_legacy_module:
            return True
        if not self.up_to_date:
            return False
        for module_name in self.deps.uses_modules:
            if module_name.split('.')[0] in {'legacy_type', 'legacy_module', 'legacy_service'}:
                continue
            file = file_dict[module_name]
            if not file.deps_up_to_date(file_dict, name_to_file):
                return False
        for module_name in self.deps.wants_code:
            file = name_to_file[module_name]
            if not file.deps_up_to_date(file_dict, name_to_file):
                return False
        return True

    def _make_module_res(self, import_list):
        return htypes.python_module.python_module(
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

    def _dep_discover_module_res(self, resource_registry, type_res_list, process):
        resource_list = [*type_res_list]

        mark_service = resource_registry['common.mark', 'mark.service']
        resource_list.append(
            htypes.import_recorder.resource(('services', 'mark'), mosaic.put(mark_service)))

        import_recorder, import_recorder_ref = self._prepare_import_recorder(process, resource_list)
        import_discoverer, import_discoverer_ref = self._prepare_import_discoverer(process)

        module_res = self._make_module_res([
                htypes.python_module.import_rec('htypes.*', import_recorder_ref),
                htypes.python_module.import_rec('services.*', import_recorder_ref),
                htypes.python_module.import_rec('*', import_discoverer_ref),
                ])
        return (import_recorder, import_discoverer, module_res)

    def _attr_collect_module_res(self, resource_registry, type_res_list, process, file_dict):
        resource_list = [*type_res_list]

        legacy_service_module = resource_registry.get_module('legacy_service')
        for service_name in legacy_service_module:
            service = resource_registry['legacy_service', service_name]
            resource_list.append(
                htypes.import_recorder.resource(('services', service_name), mosaic.put(service)))

        name_to_file = {
            file.name: file
            for file in file_dict.values()
            }

        for file in file_dict.values():
            if 'fixtures' in file.name.split('.'):
                continue
            if not file.deps_up_to_date(file_dict, name_to_file):
                continue
            resource = resource_registry[file.code_module_pair]
            resource_list.append(
                htypes.import_recorder.resource(('code', file.name), mosaic.put(resource)))
            if file.is_legacy_module:
                continue
            for service in file.deps.provides_services:
                resource = resource_registry[file.module_name, f'{service}.service']
                resource_list.append(
                    htypes.import_recorder.resource(('services', service), mosaic.put(resource)))

        import_recorder, import_recorder_ref = self._prepare_import_recorder(process, resource_list)

        module_res = self._make_module_res([
                htypes.python_module.import_rec('htypes.*', import_recorder_ref),
                htypes.python_module.import_rec('services.*', import_recorder_ref),
                htypes.python_module.import_rec('code.*', import_recorder_ref),
                ])
        return (import_recorder, module_res)

    def _imports_to_deps(self, import_set):
        wants_services = set()
        wants_code = set()
        tests_services = set()
        tests_code = set()
        for imp in import_set:
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
            provides_services=set(),
            uses_modules=set(),
            wants_services=wants_services,
            wants_code=wants_code,
            tests_services=tests_services,
            tests_code=tests_code,
            )

    def parse_source(self, import_recorder, import_discoverer, module_res, process, fail_on_incomplete):
        _log.debug("Collect attributes for: %r", self.module_name)
        collect_attributes = process.rpc_call(collect_attributes_ref)
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
        _log.info("Used import list: %s", used_imports)
        import_set = set(used_imports)
        if import_discoverer:
            discovered_imports = import_discoverer.discovered_imports()
            _log.info("Discovered import list: %s", discovered_imports)
            import_set |= set(discovered_imports)
        deps_info = self._imports_to_deps(import_set)

        if object_attrs:
            source_info = SourceInfo(
                import_name=object_attrs.object_module,
                attr_list=attr_list,
                )
        else:
            source_info = None
        return (deps_info, source_info)

    def init_deps(self, resource_registry, process, type_res_list, file_dict):
        if self.is_legacy_module or self.deps:
            return
        if self.up_to_date:
            self.deps = self.get_resource_module_deps()
        else:
            (import_recorder, import_discoverer, module_res) = self._dep_discover_module_res(
                resource_registry, type_res_list, process)
            self.deps, self.source_info = self.parse_source(
                import_recorder, import_discoverer, module_res, process, fail_on_incomplete=False)

    @staticmethod
    def service_provider_modules(resource_registry, file_dict):
        return {
            service: module_name
            for module_name, file in file_dict.items()
            if (not file.is_legacy_module
                and file.up_to_date
                and 'fixtures' not in file.name.split('.'))
            for service in file.deps.provides_services
            }

    @staticmethod
    def fixture_service_provider_modules(file):
        return {
            service: file.module_name
            for service in file.deps.provides_services
            }

    def _make_import_list(self, resource_registry, file_dict, service_provider_modules):
        code_modules = {
            file.name: file.code_module_pair
            for file in file_dict.values()
            if 'fixtures' not in file.name.split('.')
            }

        import_list = []

        for name in self.deps.wants_code:
            name_pair = code_modules[name]
            module = resource_registry[name_pair]
            import_list.append(
                htypes.python_module.import_rec(f'code.{name}', mosaic.put(module)))

        for service_name in self.deps.wants_services:
            try:
                module_name = service_provider_modules[service_name]
            except KeyError:
                service = resource_registry['legacy_service', service_name]
            else:
                service = resource_registry[module_name, f'{service_name}.service']
            import_list.append(
                htypes.python_module.import_rec(f'services.{service_name}', mosaic.put(service)))

        _log.info("Import list: %s", import_list)
        return import_list

    def _make_tested_import_list(self, resource_registry, type_res_list, process, file_dict):
        name_to_file = {
            file.name: file
            for file in file_dict.values()
            }

        name_to_recorder = {}
        import_list = []
        for name in self.deps.tests_code:
            file = name_to_file[name]
            import_recorder, module = file._attr_collect_module_res(
                resource_registry, type_res_list, process, file_dict)
            import_list.append(
                htypes.python_module.import_rec(f'tested.code.{name}', mosaic.put(module)))
            name_to_recorder[file.module_name] = import_recorder
        return (name_to_recorder, import_list)

    def _parameter_fixture(self, fixtures_file, path):
        if not fixtures_file:
            return None
        name = '.'.join([*path, 'parameter'])
        try:
            return fixtures_file.resource_module[name]
        except KeyError:
            return None

    def _visit_function(self, process, fixtures_file, object_res, attr, path):
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
                    _log.warning("Pparameter fixtures are missing for %s %s: %s", self.name, attr_path_str, missing_params)
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

        _log.info("%s %s: Retrieving type: %s", self.name, attr_path_str, call_res)
        get_resource_type = process.rpc_call(get_resource_type_ref)
        result_t = get_resource_type(resource_ref=mosaic.put(call_res))
        _log.info("%s %s type: %r", self.name, attr_path_str, result_t)

        if isinstance(result_t, htypes.inspect.coroutine_t):
            async_run = htypes.async_run.async_run(mosaic.put(call_res))
            result_t = get_resource_type(resource_ref=mosaic.put(async_run))
            _log.info("%s %s async call type: %r", self.name, attr_path_str, result_t)

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

    def _visit_object(self, process, custom_types, resource_module, fixtures_file, object_name, object_res):
        _log.debug("Collect attributes for: %s.%s", self.module_name, object_name)
        collect_attributes = process.rpc_call(collect_attributes_ref)
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
        _, get_result_t = self._visit_function(process, fixtures_file, object_res, get_attr, path=[object_name])

        for attr in attr_list:
            if attr.name == 'get':
                continue
            if not isinstance(attr, htypes.inspect.fn_attr):
                continue
            _, result_t = self._visit_function(process, fixtures_file, object_res, attr, path=[object_name])
            self._construct_method_command(custom_types, resource_module, object_name, object_dir, attr)

        return ObjectInfo(object_dir, get_result_t)

    def _visit_attribute(self, process, custom_types, resource_module, fixtures_file, module_res, attr):
        if not isinstance(attr, htypes.inspect.fn_attr):
            return None
        call_res, result_t = self._visit_function(process, fixtures_file, module_res, attr, path=[])
        if list(attr.param_list) == ['piece'] and isinstance(result_t, htypes.inspect.object_t):
            return self._visit_object(process, custom_types, resource_module, fixtures_file, attr.name, call_res)

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

        if not self.source_info:
            import_recorder, collect_module_res = self._attr_collect_module_res(
                resource_registry, type_res_list, process, file_dict)
            self.deps, self.source_info = self.parse_source(
                import_recorder, None, collect_module_res, process, fail_on_incomplete=True)

        service_providers = self.service_provider_modules(resource_registry, file_dict)
        if fixtures_file:
            service_providers.update(self.fixture_service_provider_modules(fixtures_file))
        import_list = self._make_import_list(resource_registry, file_dict, service_providers)

        import_recorder, import_recorder_ref = self._prepare_import_recorder(process, type_res_list)
        name_to_recorder, tested_import_list = self._make_tested_import_list(
            resource_registry, type_res_list, process, file_dict)

        recorder_import_list = [
            *import_list,
            htypes.python_module.import_rec('htypes.*', import_recorder_ref),
            ]
        module_res = self._make_module_res([*tested_import_list, *recorder_import_list])

        object_info_dict = {}
        for attr in self.source_info.attr_list:
            object_info = self._visit_attribute(process, custom_types, resource_module, fixtures_file, module_res, attr)
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

        return (used_types, object_info_dict)

    @staticmethod
    def _types_import_list(type_res_list, used_types):
        pair_to_resource_ref = {
            (r.name[1], r.name[2]): r.resource
            for r in type_res_list
            }
        return {
            htypes.python_module.import_rec(f'htypes.{pair[0]}.{pair[1]}', pair_to_resource_ref[pair])
            for pair in used_types
            }

    def _construct_list_spec(self, custom_types, resource_module, object_name, object_info):
        key_attribute, key_t_name = pick_key_t(object_info.get_result_t, error_prefix=f"{self.name} {object_name}")
        key_t_ref = custom_types[key_t_name.module][key_t_name.name]
        key_t_res = htypes.legacy_type.type(key_t_ref)
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
        get_resource_type = process.rpc_call(get_resource_type_ref)
        piece_t = get_resource_type(resource_ref=mosaic.put(fixture))
        _log.info("%s %s piece type: %r", self.name, object_name, piece_t)
        if not isinstance(piece_t, htypes.inspect.record_t):
            raise RuntimeError(
                f"{self.module_name}: {object_name} 'piece' parameter: Expected record type, but got: {piece_t!r}")
        piece_t_ref = custom_types[piece_t.type.module][piece_t.type.name]
        piece_t_res = htypes.legacy_type.type(piece_t_ref)
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

        pyobj_association = htypes.impl.python_object_association(
            t=mosaic.put(piece_t_res),
            function=mosaic.put(ctr_attribute),
            )
        resource_module.add_association(pyobj_association)

    def construct_resources(self, process, resource_registry, custom_types, type_res_list, tested_module_imports, file_dict, saver):
        resource_module = resource_module_factory(resource_registry, self.name)
        fixtures_file = file_dict.get(f'{self.module_name}.fixtures')

        used_types, object_info_dict = self._visit_module(
            process, resource_registry, custom_types, type_res_list, tested_module_imports, file_dict, resource_module, fixtures_file)
        # Add types discovered by tests.
        used_types |= tested_module_imports.get(self.module_name, set())

        service_providers = self.service_provider_modules(resource_registry, file_dict)
        import_list = [
            *self._make_import_list(resource_registry, file_dict, service_providers),
            *self._types_import_list(type_res_list, used_types),
            ]

        module_res = self._make_module_res(sorted(import_list))
        resource_module[f'{self.name}.module'] = module_res

        for name, object_info in object_info_dict.items():
            self._construct_object_impl(process, custom_types, resource_module, fixtures_file, module_res, name, object_info)
        for attr in self.source_info.attr_list:
            for ctr_ref in attr.constructors:
                constructor_creg.invite(ctr_ref, custom_types, resource_module, module_res, attr)

        self.set_resource_module(resource_registry, resource_module)

        source_hash = hash_sha512(self.source_path.read_bytes())
        _log.info("Write %s: %s", self.name, self.resources_path)
        saver(resource_module, self.resources_path, source_hash, self._generator_ref.hash)


process_code_module_list = [
    'common.lcs',
    'common.lcs_service',
    'resource.piece_ref',
    'ui.impl_registry',
    'ui.global_command_list',
    ]


@contextmanager
def subprocess(process_name, additional_dir_list):
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_running(
            [*module_dir_list, *additional_dir_list],
            process_code_module_list,
            rpc_endpoint,
            identity,
            process_name,
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
            resource = htypes.legacy_type.type(type_ref)
            resource_ref = mosaic.put(resource)
            resource_list.append(
                htypes.import_recorder.resource(('htypes', module_name, name), resource_ref))
    return (custom_types, resource_list)


def add_legacy_types_to_cache(resource_registry, legacy_type_modules):
    for module_name, module in legacy_type_modules.items():
        for var_name in module:
            resource_registry.add_to_cache((module_name, var_name), module[var_name])


def collect_deps(resource_registry, file_dict):
    _log.info("Collect dependencies")

    code_providers = {
        file.name: file.module_name
        for file in file_dict.values()
        }

    service_providers = {
        service: module_name
        for module_name, file in file_dict.items()
        if not file.is_legacy_module
        for service in file.deps.provides_services
        }

    deps = defaultdict(set)  # module_name -> module_name list

    for module_name, file in file_dict.items():
        if file.is_legacy_module:
            continue
        for code_name in file.deps.wants_code:
            try:
                provider = code_providers[code_name]
            except KeyError:
                raise RuntimeError(f"Module {file.module_name!r} wants code module {code_name!r}, but no one provides it")
            _log.info("%s wants code %r from: %s", module_name, code_name, provider)
            deps[module_name].add(provider)
        for service in file.deps.wants_services:
            try:
                provider = service_providers[service]
            except KeyError:
                continue  # Legacy service.
            _log.info("%s wants service %r from: %s", module_name, service, provider)
            deps[module_name].add(provider)
        base_name = '.'.join(module_name.split('.')[:-1])
        if base_name in file_dict and not file_dict[base_name].is_legacy_module:
            deps[base_name].add(module_name)  # Add fixture deps.

    # Invalidate resource modules having outdated deps.
    while True:
        have_removed_modules = False
        for module_name, dep_set in deps.items():
            file = file_dict[module_name]
            if file.is_manually_generated or not file.up_to_date:
                continue
            have_unready_deps = False
            for dep_module_name in dep_set:
                if not file_dict[dep_module_name].up_to_date:
                    _log.info("Resource module %s dep %s is not ready", module_name, dep_module_name)
                    have_unready_deps = True
            if have_unready_deps:
                file.invalidate_resource_module(resource_registry)
                have_removed_modules = True
        if not have_removed_modules:
            break

    for module_name, dep_set in sorted(deps.items()):
        _log.info("Dep: %s -> %s", module_name, ', '.join(dep_set))

    return deps


def collect_source_files(generator_ref, subdir_list, root_dirs, resource_registry):
    file_dict = {}

    def add_source_files(root, dir):
        for path in dir.rglob('*.dyn.py'):
            if 'test' in path.relative_to(root).parts:
                continue
            source_file = SourceFile(generator_ref, root, path)
            source_file.init_resource_module(resource_registry)
            file_dict[source_file.module_name] = source_file

    for subdir in subdir_list:
        add_source_files(hyperapp_dir, hyperapp_dir / subdir)
    for root in root_dirs:
        add_source_files(root, root)

    return file_dict


def init_deps(resource_registry, process, type_res_list, file_dict):
    for file in file_dict.values():
        file.init_deps(resource_registry, process, type_res_list, file_dict)


def ready_for_construction_files(file_dict, deps):
    for module_name, file in sorted(file_dict.items()):
        if file.is_legacy_module:
            continue
        if file.up_to_date:
            continue
        not_ready_deps = [
            d for d in deps[module_name]
            if not file_dict[d].up_to_date
            ]
        if not_ready_deps:
            _log.info("Deps are not ready for %s: %s", module_name, ", ".join(not_ready_deps))
            continue
        yield file


def resource_saver(resource_module, path, source_hash, generator_hash):
    resource_module.save_as(path, source_hash, generator_hash)


def update_resources(generator_ref, subdir_list, root_dirs, module_list, process_name='update-resources-runner', saver=resource_saver):
    resource_dir_list = [hyperapp_dir / d for d in subdir_list] + root_dirs
    resource_registry = resource_registry_factory()

    custom_types, type_res_list = legacy_type_resources(resource_dir_list)
    legacy_type_modules = legacy_type_resource_loader(custom_types)
    add_legacy_types_to_cache(resource_registry, legacy_type_modules)
    resource_registry.update_modules(legacy_type_modules)

    custom_modules = local_modules.copy()
    code_module_loader.load_code_modules(custom_types, resource_dir_list, custom_modules)
    _log.info("Custom modules: %s", ", ".join(custom_modules.by_name.keys()))
    resource_registry.update_modules(legacy_module_resource_loader(custom_modules))

    resource_registry.set_module('legacy_service', legacy_service_resource_loader(resource_registry, custom_modules))

    tested_module_imports = {}  # module name -> type import tuple set

    with subprocess(process_name, resource_dir_list) as process:

        file_dict = collect_source_files(generator_ref, subdir_list, root_dirs, resource_registry)
        init_deps(resource_registry, process, type_res_list, file_dict)

        round = 0
        idx = 0
        while True:
            _log.info("****** Round #%d  %s", round, '*'*50)
            deps = collect_deps(resource_registry, file_dict)
            ready_files = list(sorted(
                ready_for_construction_files(file_dict, deps), key=attrgetter('module_name')))
            ready_module_names = [f.module_name for f in ready_files]
            _log.info("Ready for construction: %s", ", ".join(ready_module_names))
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
