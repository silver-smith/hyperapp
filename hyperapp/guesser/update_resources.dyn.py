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


Source = namedtuple('Source', 'import_name attr_list want_services want_code tests_services tests_code')
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
    return resource_list


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

    want_services = set()
    want_code = set()
    tests_services = set()
    tests_code = set()
    for imp in discovered_imports:
        if len(imp) < 2:
            continue
        kind, name, *_ = imp
        if kind == 'services':
            want_services.add(name)
            continue
        if kind == 'code':
            want_code.add(name)
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
    _log.info("Discovered import deps: want_services: %s", want_services)
    _log.info("Discovered import deps: want_code: %s", want_code)
    _log.info("Discovered import deps: tests_services: %s", tests_services)
    _log.info("Discovered import deps: tests_code: %s", tests_code)

    return Source(
        import_name=object_attrs.object_module,
        attr_list=attr_list,
        want_services=want_services,
        want_code=want_code,
        tests_services=tests_services,
        tests_code=tests_code,
        )


def load_deps_from_resource(resource_registry, module_name, res_path):
    res_module = resource_module_factory(resource_registry, module_name, res_path)
    return {
        name for name in res_module.used_modules
        if name.split('.')[0] not in {'legacy_type', 'legacy_service', 'legacy_module'}
        }


def process_file(process, type_res_list, resource_registry, root_dir, source_path):
    stem = source_path.name[:-len('.dyn.py')]
    module_name = str(source_path.relative_to(root_dir).with_name(stem)).replace('/', '.')
    yaml_path = source_path.with_name(stem + '.yaml')
    if yaml_path.exists():
        _log.debug("%s: legacy module", source_path)
        return FileInfo(module_name, source_path, None, None)
    res_path = source_path.with_name(stem + '.resources.yaml')
    if res_path.exists() and not res_path.read_text().startswith(AUTO_GEN_LINE):
        _log.debug("%s: manually generated", source_path)
        return FileInfo(module_name, source_path, res_path, None)
    # if res_path.exists():
    #     used_modules = load_deps_from_resource(resource_registry, module_name, res_path)
    #     _log.info("%s: %s", path, ', '.join(used_modules))
    # else:
    #     _log.info("%s: no resources", path)
    #     used_modules = set()
    source_info = load_file_deps(process, type_res_list, module_name, source_path)
    return FileInfo(module_name, source_path, res_path, source_info)


def construct_resources(process, file):
    _log.info("Construct resources for: %s", file.name)


def update_resources(root_dir, subdir_list):
    additional_dir_list = [root_dir / d for d in subdir_list]
    resource_registry = resource_registry_factory()
    dep_dict = defaultdict(set)
    up_to_date = set()  # module_name set
    file_dict = {}

    type_res_list = legacy_type_resources(root_dir, subdir_list)

    with subprocess(additional_dir_list) as process:

        for subdir in subdir_list:
            for path in root_dir.joinpath(subdir).rglob('*.dyn.py'):
                if 'test' in path.parts:
                    continue
                file = process_file(process, type_res_list, resource_registry, root_dir, path)
                if not file.source:
                    up_to_date.add(file.name)
                    continue
                _log.debug("File: %s", file)
                dep_dict[file.name] |= file.source.want_code
                file_dict[file.name] = file

        for name in file_dict:
            base_name = '.'.join(name.split('.')[:-1])
            if base_name in file_dict:
                dep_dict[base_name].add(name)
        for name, deps in sorted(dep_dict.items()):
            _log.info("Dep: %s -> %s", name, ', '.join(deps))
        _log.info("Up-to-date: %s", up_to_date)

        for name, dep_list in sorted(dep_dict.items()):
            if not all(dep in up_to_date for dep in dep_list):
                continue
            construct_resources(process, file_dict[name])
