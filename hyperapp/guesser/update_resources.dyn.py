import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from functools import cached_property

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from hyperapp.common.ref import hash_sha512

from . import htypes
from .services import (
    code_module_loader,
    collect_attributes_ref,
    constructor_creg,
    endpoint_registry,
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
    web,
    )

_log = logging.getLogger(__name__)


SourceInfo = namedtuple('SourceInfo', 'import_name attr_list')
DepsInfo = namedtuple('DepsInfo', 'provides_services uses_modules wants_services wants_code tests_services tests_code')


class SourceFile:

    def __init__(self, root_dir, source_path):
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
        if resource_module.source_hash == source_hash:
            _log.info("%s: up to date", self.module_name)
            return True
        _log.info("%s: changed", self.module_name)
        return False

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

    def parse_source(self, resource_registry, process, type_res_list, file_dict):
        resource_list = [*type_res_list]

        name_to_file = {
            file.name: file
            for file in file_dict.values()
            }

        for file in file_dict.values():
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

        import_recorder_res = htypes.import_recorder.import_recorder(resource_list)
        import_recorder_ref = mosaic.put(import_recorder_res)
        import_recorder = process.proxy(import_recorder_ref)
        import_recorder.reset()

        import_discoverer_res = htypes.import_discoverer.import_discoverer()
        import_discoverer_ref = mosaic.put(import_discoverer_res)
        import_discoverer = process.proxy(import_discoverer_ref)
        import_discoverer.reset()

        module_res = htypes.python_module.python_module(
            module_name=self.module_name,
            source=self.source_path.read_text(),
            file_path=str(self.source_path),
            import_list=[
                htypes.python_module.import_rec('htypes.*', import_recorder_ref),
                htypes.python_module.import_rec('services.*', import_recorder_ref),
                htypes.python_module.import_rec('code.*', import_recorder_ref),
                htypes.python_module.import_rec('*', import_discoverer_ref),
                ],
            )

        collect_attributes = process.rpc_call(collect_attributes_ref)
        object_attrs = collect_attributes(object_ref=mosaic.put(module_res))
        attr_list = [web.summon(ref) for ref in object_attrs.attr_list]
        _log.info("Collected attrs for %r, module %s: %s", self.module_name, object_attrs.object_module, attr_list)

        discovered_imports = import_discoverer.discovered_imports()
        _log.info("Discovered import list: %s", discovered_imports)

        used_imports = import_recorder.used_imports()
        _log.info("Used import list: %s", used_imports)

        wants_services = set()
        wants_code = set()
        tests_services = set()
        tests_code = set()
        for imp in discovered_imports + used_imports:
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

        deps_info = DepsInfo(
            provides_services=set(),
            uses_modules=set(),
            wants_services=wants_services,
            wants_code=wants_code,
            tests_services=tests_services,
            tests_code=tests_code,
            )
        source_info = SourceInfo(
            import_name=object_attrs.object_module,
            attr_list=attr_list,
            )
        return (deps_info, source_info)

    def init_deps(self, resource_registry, process, type_res_list, file_dict):
        if self.is_legacy_module or self.deps:
            return
        if self.up_to_date:
            self.deps = self.get_resource_module_deps()
        else:
            self.deps, self.source_info = self.parse_source(resource_registry, process, type_res_list, file_dict)

    def make_module_res(self, import_list):
        return htypes.python_module.python_module(
            module_name=self.name,
            source=self.source_path.read_text(),
            file_path=str(self.source_path),
            import_list=tuple(sorted(import_list)),
            )

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

    def make_import_list(self, resource_registry, file_dict, service_provider_modules):
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

    def discover_type_imports(self, process, resource_registry, type_res_list, file_dict):
        service_providers = self.service_provider_modules(resource_registry, file_dict)
        fixtures_file = file_dict.get(f'{self.module_name}.fixtures')
        if fixtures_file:
            service_providers.update(self.fixture_service_provider_modules(fixtures_file))
        import_list = self.make_import_list(resource_registry, file_dict, service_providers)

        import_recorder_res = htypes.import_recorder.import_recorder(type_res_list)
        import_recorder_ref = mosaic.put(import_recorder_res)
        import_recorder = process.proxy(import_recorder_ref)
        import_recorder.reset()

        recorder_import_list = [
            *import_list,
            htypes.python_module.import_rec('htypes.*', import_recorder_ref),
            ]
        resource_module = resource_module_factory(resource_registry, self.name)
        module_res = self.make_module_res(recorder_import_list)

        for attr in self.source_info.attr_list:
            if not isinstance(attr, htypes.inspect.fn_attr):
                continue
            attr_res = htypes.attribute.attribute(
                object=mosaic.put(module_res),
                attr_name=attr.name,
                )
            if attr.param_list:
                continue  # TODO: Fixtures.
            call_res = htypes.call.call(mosaic.put(attr_res))

            get_resource_type = process.rpc_call(get_resource_type_ref)
            result_t = get_resource_type(resource_ref=mosaic.put(call_res))
            _log.info("%s/%s type: %r", self.name, attr.name, result_t)

        used_imports = import_recorder.used_imports()
        _log.info("Used import list: %s", used_imports)

        used_types = set()
        for imp in used_imports:
            if len(imp) < 3:
                continue
            kind, module, name = imp
            if kind != 'htypes':
                continue
            used_types.add((module, name))
        _log.info("Discovered import htypes: %s", used_types)
        return used_types

    @staticmethod
    def types_import_list(type_res_list, used_types):
        pair_to_resource_ref = {
            (r.name[1], r.name[2]): r.resource
            for r in type_res_list
            }
        return {
            htypes.python_module.import_rec(f'htypes.{pair[0]}.{pair[1]}', pair_to_resource_ref[pair])
            for pair in used_types
            }

    def construct_resources(self, process, resource_registry, custom_types, type_res_list, file_dict):
        used_types = self.discover_type_imports(process, resource_registry, type_res_list, file_dict)

        service_providers = self.service_provider_modules(resource_registry, file_dict)
        import_list = [
            *self.make_import_list(resource_registry, file_dict, service_providers),
            *self.types_import_list(type_res_list, used_types),
            ]

        resource_module = resource_module_factory(resource_registry, self.name)
        module_res = self.make_module_res(import_list)
        resource_module[f'{self.name}.module'] = module_res

        for attr in self.source_info.attr_list:
            for ctr_ref in attr.constructors:
                constructor_creg.invite(ctr_ref, custom_types, resource_module, module_res, attr)

        self.set_resource_module(resource_registry, resource_module)

        source_hash = hash_sha512(self.source_path.read_bytes())
        _log.info("Write %s: %s", self.name, self.resources_path)
        resource_module.save_as(self.resources_path, source_hash)


process_code_module_list = [
    'common.lcs',
    'common.lcs_service',
    'ui.impl_registry',
    'ui.global_command_list',
    ]


@contextmanager
def subprocess(additional_dir_list):
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_running(
            [*module_dir_list, *additional_dir_list],
            process_code_module_list,
            rpc_endpoint,
            identity,
            'update_resources',
        ) as process:
        yield process


def legacy_type_resources(root_dir, subdir_list):
    custom_types = {**local_types}
    dir_list = [root_dir / d for d in subdir_list]
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
    _log.info("Collect deps")

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
            provider = code_providers[code_name]
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


def collect_source_files(root_dir, subdir_list, resource_registry):
    file_dict = {}
    for subdir in subdir_list:
        for path in root_dir.joinpath(subdir).rglob('*.dyn.py'):
            if 'test' in path.parts:
                continue
            source_file = SourceFile(root_dir, path)
            source_file.init_resource_module(resource_registry)
            file_dict[source_file.module_name] = source_file
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


def update_resources(root_dir, subdir_list):
    additional_dir_list = [root_dir / d for d in subdir_list]
    resource_registry = resource_registry_factory()

    custom_types, type_res_list = legacy_type_resources(root_dir, subdir_list)
    legacy_type_modules = legacy_type_resource_loader(custom_types)
    add_legacy_types_to_cache(resource_registry, legacy_type_modules)
    resource_registry.update_modules(legacy_type_modules)

    custom_modules = local_modules.copy()
    code_module_loader.load_code_modules(custom_types, [root_dir / d for d in subdir_list], custom_modules)
    _log.info("Custom modules: %s", ", ".join(custom_modules.by_name.keys()))
    resource_registry.update_modules(legacy_module_resource_loader(custom_modules))

    resource_registry.set_module('legacy_service', legacy_service_resource_loader(resource_registry, custom_modules))

    with subprocess(additional_dir_list) as process:

        file_dict = collect_source_files(root_dir, subdir_list, resource_registry)
        init_deps(resource_registry, process, type_res_list, file_dict)
        deps = collect_deps(resource_registry, file_dict)

        idx = 0
        for file in ready_for_construction_files(file_dict, deps):
            # if file.name != 'meta_registry_association':
            #     continue
            _log.info("****** #%d Construct resources for: %s  %s", idx, file.module_name, '*'*50)
            file.construct_resources(process, resource_registry, custom_types, type_res_list, file_dict)
            idx += 1
            # return
