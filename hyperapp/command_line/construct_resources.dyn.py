import logging

log = logging.getLogger(__name__)

from .services import (
    hyperapp_dir,
    )


def construct_resources(source_path_list):
    for path in source_path_list:
        rel_path = path.absolute().relative_to(hyperapp_dir)
        ext = '.dyn.py'
        if rel_path.name.endswith(ext):
            stem = rel_path.name[:-len(ext)]
            name = str(rel_path.with_name(stem)).replace('/', '.')
        else:
            log.error(f"Source file name should end with %r: %s", ext, path)
            continue
        log.info("Construct resources for: %s @ %s", name, hyperapp_dir)
        resource_module = services.construct_resources(name, rel_path, hyperapp_dir)
        res_path = path.with_name(stem + '.resources.yaml')
        resource_module.save_as(res_path)
        log.info("Written resource file: %s", res_path)
