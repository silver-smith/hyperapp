import logging

from .services import (
    resource_module_factory,
    resource_registry_factory,
    )

_log = logging.getLogger(__name__)


AUTO_GEN_LINE = '# Automatically generated file. Do not edit.'


def process_file(resource_registry, path):
    stem = path.name[:-len('.dyn.py')]
    yaml_path = path.with_name(stem + '.yaml')
    if yaml_path.exists():
        _log.debug("%s: legacy module", path)
        return
    res_path = path.with_name(stem + '.resources.yaml')
    if res_path.exists() and not res_path.read_text().startswith(AUTO_GEN_LINE):
        _log.debug("%s: manually generated", path)
        return
    if not res_path.exists():
        _log.info("%s: no resources", path)
        return
    res_module = resource_module_factory(resource_registry, stem, res_path)
    used_modules = {
        name for name in res_module.used_modules
        if name.split('.')[0] not in {'legacy_type', 'legacy_service', 'legacy_module'}
        }
    _log.info("%s: %s", path, ', '.join(used_modules))


def update_resources(root_dir, resource_dir_list, source_dir_list):
    resource_registry = resource_registry_factory()
    for dir in source_dir_list:
        for path in dir.rglob('*.dyn.py'):
            process_file(resource_registry, path)
