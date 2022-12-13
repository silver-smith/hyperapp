import logging
from collections import defaultdict, namedtuple

from .services import (
    resource_module_factory,
    resource_registry_factory,
    )

_log = logging.getLogger(__name__)


AUTO_GEN_LINE = '# Automatically generated file. Do not edit.'


FileInfo = namedtuple('FileInfo', 'name source_path resources_path used_modules')


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


def update_resources(root_dir, resource_dir_list, source_dir_list):
    resource_registry = resource_registry_factory()
    deps = defaultdict(set)
    file_dict = {}
    for dir in source_dir_list:
        for path in dir.rglob('*.dyn.py'):
            file = process_file(resource_registry, path)
            if not file:
                continue
            _log.info("File: %s", file)
            deps[file.name] |= file.used_modules
            file_dict[file.name] = file
    for name in file_dict:
        base_name = '.'.join(name.split('.')[:-1])
        if base_name in file_dict:
            deps[base_name].add(name)
    for name, deps in sorted(deps.items()):
        _log.info("Dep: %s -> %s", name, ', '.join(deps))
