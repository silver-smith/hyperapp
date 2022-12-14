import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager

from . import htypes
from .services import (
    collect_attributes_ref,
    endpoint_registry,
    generate_rsa_identity,
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


FileInfo = namedtuple('FileInfo', 'name source_path resources_path used_modules')

process_code_module_list = [
    'common.lcs',
    'common.lcs_service',
    'ui.impl_registry',
    'ui.global_command_list',
    ]


def update_resources(root_dir, subdir_list):
    additional_dir_list = [root_dir / d for d in subdir_list]
    resource_registry = resource_registry_factory()
    deps = defaultdict(set)
    file_dict = {}
    for subdir in subdir_list:
        for path in root_dir.joinpath(subdir).rglob('*.dyn.py'):
            file = process_file(resource_registry, path)
            if not file:
                continue
            _log.debug("File: %s", file)
            deps[file.name] |= file.used_modules
            file_dict[file.name] = file
    for name in file_dict:
        base_name = '.'.join(name.split('.')[:-1])
        if base_name in file_dict:
            deps[base_name].add(name)
    for name, deps in sorted(deps.items()):
        _log.info("Dep: %s -> %s", name, ', '.join(deps))

    type_res_list = legacy_type_resources(root_dir, subdir_list)

    with subprocess(additional_dir_list) as process:
        for file in file_dict.values():
            load_file_deps(process, type_res_list, file)


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


def process_file(resource_registry, path):
    stem = path.name[:-len('.dyn.py')]
    yaml_path = path.with_name(stem + '.yaml')
    if yaml_path.exists():
        _log.debug("%s: legacy module", path)
        return None
    res_path = path.with_name(stem + '.resources.yaml')
    if res_path.exists() and not res_path.read_text().startswith(AUTO_GEN_LINE):
        _log.debug("%s: manually generated", path)
        return None
    if res_path.exists():
        res_module = resource_module_factory(resource_registry, stem, res_path)
        used_modules = {
            name for name in res_module.used_modules
            if name.split('.')[0] not in {'legacy_type', 'legacy_service', 'legacy_module'}
            }
        _log.info("%s: %s", path, ', '.join(used_modules))
    else:
        _log.info("%s: no resources", path)
        used_modules = set()
    return FileInfo(stem, path, res_path, used_modules)


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
    return resource_list


def load_file_deps(process, type_res_list, file):
    import_recorder_res = htypes.import_recorder.import_recorder(type_res_list)
    import_recorder_ref = mosaic.put(import_recorder_res)

    import_discoverer_res = htypes.import_discoverer.import_discoverer()
    import_discoverer_ref = mosaic.put(import_discoverer_res)

    module_res = htypes.python_module.python_module(
        module_name=file.name,
        source=file.source_path.read_text(),
        file_path=str(file.source_path),
        import_list=[
            htypes.python_module.import_rec('htypes.*', import_recorder_ref),
            htypes.python_module.import_rec('*', import_discoverer_ref),
            ],
        )

    collect_attributes = process.rpc_call(collect_attributes_ref)
    object_attrs = collect_attributes(object_ref=mosaic.put(module_res))
    attr_list = [web.summon(ref) for ref in object_attrs.attr_list]
    _log.info("Collected attr list, module %s: %s", object_attrs.object_module, attr_list)
