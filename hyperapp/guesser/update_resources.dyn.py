import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from hyperapp.common.ref import hash_sha512

from . import htypes
from .services import (
    code_module_loader,
    collect_attributes_ref,
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
DepsInfo = namedtuple('DepsInfo', 'provide_services wants_services wants_code tests_services tests_code')
FileInfo = namedtuple('FileInfo', 'name source_path resources_path deps_info source_info', defaults=[None, None, None])


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


def parse_source(process, type_res_list, module_name, source_path):
    import_recorder_res = htypes.import_recorder.import_recorder(type_res_list)
    import_recorder_ref = mosaic.put(import_recorder_res)

    import_discoverer_res = htypes.import_discoverer.import_discoverer()
    import_discoverer_ref = mosaic.put(import_discoverer_res)
    import_discoverer = process.proxy(import_discoverer_ref)
    import_discoverer.reset()

    module_res = htypes.python_module.python_module(
        module_name=module_name,
        source=source_path.read_text(),
        file_path=str(source_path),
        import_list=[
            htypes.python_module.import_rec('htypes.*', import_recorder_ref),
            htypes.python_module.import_rec('*', import_discoverer_ref),
            ],
        )

    collect_attributes = process.rpc_call(collect_attributes_ref)
    object_attrs = collect_attributes(object_ref=mosaic.put(module_res))
    attr_list = [web.summon(ref) for ref in object_attrs.attr_list]
    _log.info("Collected attrs for %r, module %s: %s", module_name, object_attrs.object_module, attr_list)

    discovered_imports = import_discoverer.discovered_imports()
    _log.info("Discovered import list: %s", discovered_imports)

    wants_services = set()
    wants_code = set()
    tests_services = set()
    tests_code = set()
    for imp in discovered_imports:
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
        _log.warning("Unknown import kind (old-style import?): %r at %s", kind, source_path)
    _log.info("Discovered import deps: wants_services: %s", wants_services)
    _log.info("Discovered import deps: wants_code: %s", wants_code)
    _log.info("Discovered import deps: tests_services: %s", tests_services)
    _log.info("Discovered import deps: tests_code: %s", tests_code)

    deps_info = DepsInfo(
        provide_services=set(),
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



def deps_from_module(resource_module):
    return DepsInfo(
        provide_services=resource_module.provided_services,
        wants_services=set(),
        wants_code=set(),
        tests_services=set(),
        tests_code=set(),
        )


def resource_module_deps(resource_registry, module_name, res_module):
    return {
        name for name in res_module.used_modules
        if name.split('.')[0] not in {'legacy_type', 'legacy_service', 'legacy_module'}
        }


def is_up_to_date(module_name, source_path, resource_module):
    if not resource_module.is_auto_generated:
        _log.info("%s: manually generated", module_name)
        return True
    if not resource_module.source_hash:
        _log.info("%s: no source hash", module_name)
        return False
    source_hash = hash_sha512(source_path.read_bytes())
    if resource_module.source_hash == source_hash:
        _log.info("%s: up to date", module_name)
        return True
    _log.info("%s: changed", module_name)
    return False


def process_file(process, type_res_list, resource_registry, root_dir, source_path, file_dict, res_modules, code_modules):
    stem = source_path.name[:-len('.dyn.py')]
    module_name = str(source_path.relative_to(root_dir).with_name(stem)).replace('/', '.')
    yaml_path = source_path.with_name(stem + '.yaml')
    if yaml_path.exists():
        _log.debug("%s: legacy module", source_path)
        file_dict[module_name] =  FileInfo(module_name, source_path)
        code_modules[module_name] = (f'legacy_module.{module_name}', stem)
        return
    code_modules[module_name] = (module_name, f'{stem}.module')
    resources_path = source_path.with_name(stem + '.resources.yaml')
    if resources_path.exists():
        resource_module = resource_module_factory(resource_registry, module_name, resources_path)
        if is_up_to_date(module_name, source_path, resource_module):
            deps_info = deps_from_module(resource_module)
            file_dict[module_name] = FileInfo(module_name, source_path, resources_path, deps_info)
            res_modules[module_name] = resource_module
            resource_registry.set_module(module_name, resource_module)
            return
    deps_info, source_info  = parse_source(process, type_res_list, module_name, source_path)
    file_dict[module_name] = FileInfo(module_name, source_path, resources_path, deps_info, source_info)


def make_module_res(file, local_name, import_list):
    return htypes.python_module.python_module(
        module_name=local_name,
        source=file.source_path.read_text(),
        file_path=str(file.source_path),
        import_list=tuple(sorted(import_list)),
        )


def discover_type_imports(process, resource_registry, file, local_name, type_res_list, import_list):
    import_recorder_res = htypes.import_recorder.import_recorder(type_res_list)
    import_recorder_ref = mosaic.put(import_recorder_res)
    recorder_import_list = [
        htypes.python_module.import_rec('htypes.*', import_recorder_ref),
        *import_list,
        ]
    resource_module = resource_module_factory(resource_registry, file.name)
    module_res = make_module_res(file, local_name, recorder_import_list)
    # resource_module[f'{local_name}.module'] = module_res

    for attr in file.source_info.attr_list:
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
        _log.info("%s/%s type: %r", file.name, attr.name, result_t)


def collect_deps(resource_registry, file_dict, res_modules, name_to_full_name):
    _log.info("Collect deps")

    dep_dict = defaultdict(set)

    service_providers = {
        service: file.name
        for file in file_dict.values()
        if file.deps_info
        for service in file.deps_info.provide_services
        }

    for name, file in file_dict.items():
        if file.deps_info:
            for code_name in file.deps_info.wants_code:
                full_code_name = name_to_full_name[code_name]
                _log.info("%s wants code %r from: %s", name, code_name, full_code_name)
                dep_dict[file.name].add(full_code_name)
            for service in file.deps_info.wants_services:
                try:
                    provider = service_providers[service]
                except KeyError:
                    continue  # Legacy service.
                _log.info("%s wants service %r from: %s", name, service, provider)
                dep_dict[file.name].add(provider)
        base_name = '.'.join(name.split('.')[:-1])
        if base_name in file_dict:
            dep_dict[base_name].add(name)

    # Remove resource modules having missing deps.
    have_removed_modules = True
    while have_removed_modules:
        have_removed_modules = False
        for module_name, res_module in list(res_modules.items()):
            used_modules = resource_module_deps(resource_registry, module_name, res_module)
            for name in used_modules:
                if name not in res_modules:
                    _log.info("Resource module %s dep %s is not ready", module_name, name)
                    del res_modules[module_name]
                    have_removed_modules = True
                    break

    return dep_dict


def construct_resources(process, resource_registry, type_res_list, name_to_full_name, code_modules, file):
    _log.info("Construct resources for: %s", file.name)

    service_resources = {}
    for module_name, var_name in resource_registry:
        l = var_name.split('.')
        if len(l) == 2 and l[1] == 'service':
            service_resources[l[1]] = resource_registry[module_name, var_name]

    import_list = []
    for code_name in file.deps_info.wants_code:
        name = name_to_full_name[code_name]
        code_path = code_modules[name]
        code_module = resource_registry[code_path]
        import_list.append(
            htypes.python_module.import_rec(f'code.{code_name}', mosaic.put(code_module)))
    for service_name in file.deps_info.wants_services:
        try:
            service = service_resources[service_name]
        except KeyError:
            service = resource_registry['legacy_service', service_name]
        import_list.append(
            htypes.python_module.import_rec(f'services.{service_name}', mosaic.put(service)))
    _log.info("Import list: %s", import_list)

    local_name = file.name.split('.')[-1]

    discover_type_imports(process, resource_registry, file, local_name, type_res_list, import_list)

    resource_module = resource_module_factory(resource_registry, file.name)
    resource_module[f'{local_name}.module'] = make_module_res(file, local_name, import_list)

    source_hash = hash_sha512(file.source_path.read_bytes())
    _log.info("Write %s: %s", file.name, file.resources_path)
    resource_module.save_as(file.resources_path, source_hash)


def update_resources(root_dir, subdir_list):
    additional_dir_list = [root_dir / d for d in subdir_list]
    resource_registry = resource_registry_factory()
    file_dict = {}  # full name -> FileInfo.
    res_modules = {}  # full name -> resource module.
    code_modules = {}  # full name -> code module path.

    custom_types, type_res_list = legacy_type_resources(root_dir, subdir_list)
    resource_registry.update_modules(legacy_type_resource_loader(custom_types))

    custom_modules = local_modules.copy()
    code_module_loader.load_code_modules(custom_types, [root_dir / d for d in subdir_list], custom_modules)
    _log.info("Custom modules: %s", ", ".join(custom_modules.by_name.keys()))
    resource_registry.update_modules(legacy_module_resource_loader(custom_modules))

    resource_registry.set_module('legacy_service', legacy_service_resource_loader(resource_registry, custom_modules))

    with subprocess(additional_dir_list) as process:

        for subdir in subdir_list:
            for path in root_dir.joinpath(subdir).rglob('*.dyn.py'):
                if 'test' in path.parts:
                    continue
                process_file(process, type_res_list, resource_registry, root_dir, path, file_dict, res_modules, code_modules)

        name_to_full_name = {
            name.split('.')[-1]: name
            for name in file_dict.keys()
            }

        dep_dict = collect_deps(resource_registry, file_dict, res_modules, name_to_full_name)

        for name, deps in sorted(dep_dict.items()):
            _log.info("Dep: %s -> %s", name, ', '.join(deps))
        _log.info("Resource modules: %s", ", ".join(res_modules.keys()))
        _log.info("Code modules: %s", code_modules)

        for name, file in sorted(file_dict.items()):
            if not file.source_info:
                continue  # Legacy module or manual.
            if name in res_modules:
                continue  # Already made.
            not_ready_deps = [
                dep for dep in dep_dict[name]
                if file_dict[dep].resources_path and dep not in res_modules
                ]
            if not_ready_deps:
                _log.info("Deps are not ready for %s: %s", name, ", ".join(not_ready_deps))
                continue
            construct_resources(process, resource_registry, type_res_list, name_to_full_name, code_modules, file_dict[name])
            return
