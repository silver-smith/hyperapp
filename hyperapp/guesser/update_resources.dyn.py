import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager

from . import htypes
from .services import (
    code_module_loader,
    collect_attributes_ref,
    endpoint_registry,
    generate_rsa_identity,
    legacy_module_resource_loader,
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


AUTO_GEN_LINE = '# Automatically generated file. Do not edit.'


Source = namedtuple('Source', 'import_name attr_list wants_services wants_code tests_services tests_code')
FileInfo = namedtuple('FileInfo', 'name source_path resources_path source')


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


def load_file_deps(process, type_res_list, module_name, source_path):
    import_recorder_res = htypes.import_recorder.import_recorder(type_res_list)
    import_recorder_ref = mosaic.put(import_recorder_res)

    import_discoverer_res = htypes.import_discoverer.import_discoverer()
    import_discoverer_ref = mosaic.put(import_discoverer_res)

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

    import_discoverer = process.proxy(import_discoverer_ref)
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

    return Source(
        import_name=object_attrs.object_module,
        attr_list=attr_list,
        wants_services=wants_services,
        wants_code=wants_code,
        tests_services=tests_services,
        tests_code=tests_code,
        )


def load_deps_from_resource(resource_registry, module_name, res_path):
    res_module = resource_module_factory(resource_registry, module_name, res_path)
    return {
        name for name in res_module.used_modules
        if name.split('.')[0] not in {'legacy_type', 'legacy_service', 'legacy_module'}
        }


def process_file(process, type_res_list, resource_registry, root_dir, source_path, file_dict, res_modules, code_modules):
    stem = source_path.name[:-len('.dyn.py')]
    module_name = str(source_path.relative_to(root_dir).with_name(stem)).replace('/', '.')
    yaml_path = source_path.with_name(stem + '.yaml')
    if yaml_path.exists():
        _log.debug("%s: legacy module", source_path)
        file_dict[module_name] =  FileInfo(module_name, source_path, None, None)
        code_modules[module_name] = (f'legacy_module.{module_name}', stem)
        return
    code_modules[module_name] = (module_name, f'{stem}.module')
    res_path = source_path.with_name(stem + '.resources.yaml')
    if res_path.exists() and not res_path.read_text().startswith(AUTO_GEN_LINE):
        _log.debug("%s: manually generated", source_path)
        file_dict[module_name] = FileInfo(module_name, source_path, res_path, None)
        res_module = resource_module_factory(resource_registry, module_name, res_path)
        res_modules[module_name] = res_module
        resource_registry.set_module(module_name, res_module)
        return
    # if res_path.exists():
    #     used_modules = load_deps_from_resource(resource_registry, module_name, res_path)
    #     _log.info("%s: %s", path, ', '.join(used_modules))
    # else:
    #     _log.info("%s: no resources", path)
    #     used_modules = set()
    source_info = load_file_deps(process, type_res_list, module_name, source_path)
    file_dict[module_name] = FileInfo(module_name, source_path, res_path, source_info)


def construct_resources(process, resource_registry, type_res_list, name_to_full_name, code_modules, file):
    _log.info("Construct resources for: %s", file.name)

    import_recorder_res = htypes.import_recorder.import_recorder(type_res_list)
    import_recorder_ref = mosaic.put(import_recorder_res)

    import_list = [
        htypes.python_module.import_rec('htypes.*', import_recorder_ref),
        ]
    for code_name in file.source.wants_code:
        name = name_to_full_name[code_name]
        code_path = code_modules[name]
        code_module = resource_registry[code_path]
        import_list.append(
            htypes.python_module.import_rec(f'code.{code_name}', mosaic.put(code_module)))
    _log.info("Import list: %s", import_list)

    module_res = htypes.python_module.python_module(
        module_name=module_name,
        source=source_path.read_text(),
        file_path=str(source_path),
        import_list=import_list,
        )


def update_resources(root_dir, subdir_list):
    additional_dir_list = [root_dir / d for d in subdir_list]
    resource_registry = resource_registry_factory()
    dep_dict = defaultdict(set)
    file_dict = {}  # full name -> FileInfo.
    res_modules = {}  # full name -> resource module.
    code_modules = {}  # full name -> code module path.

    custom_types, type_res_list = legacy_type_resources(root_dir, subdir_list)
    resource_registry.update_modules(legacy_type_resource_loader(custom_types))

    custom_modules = local_modules.copy()
    code_module_loader.load_code_modules(custom_types, [root_dir / d for d in subdir_list], custom_modules)
    _log.info("Custom modules: %s", ", ".join(custom_modules.by_name.keys()))
    resource_registry.update_modules(legacy_module_resource_loader(custom_modules))

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

        for name, file in file_dict.items():
            if file.source:
                for code_name in file.source.wants_code:
                    dep_dict[file.name].add(name_to_full_name[code_name])
            base_name = '.'.join(name.split('.')[:-1])
            if base_name in file_dict:
                dep_dict[base_name].add(name)

        for name, deps in sorted(dep_dict.items()):
            _log.info("Dep: %s -> %s", name, ', '.join(deps))
        _log.info("Resource modules: %s", ", ".join(res_modules.keys()))
        _log.info("Code modules: %s", code_modules)

        for name, file in sorted(file_dict.items()):
            if not file.resources_path:
                continue  # Legacy module.
            if name in res_modules:
                continue  # Already made.
            if not all(dep in res_modules or not file_dict[dep].resources_path for dep in dep_dict[name]):
                _log.info("Deps are not ready for: %s", name)
                continue
            construct_resources(process, resource_registry, type_res_list, name_to_full_name, code_modules, file_dict[name])
