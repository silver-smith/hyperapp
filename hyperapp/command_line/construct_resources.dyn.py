import logging

log = logging.getLogger(__name__)

from .services import (
    hyperapp_dir,
    )


def construct_resources(source_path_list):
    for path in source_path_list:
        abs_path = path.absolute()
        rel_path = abs_path.relative_to(hyperapp_dir)
        ext = '.dyn.py'
        if rel_path.name.endswith(ext):
            stem = rel_path.name[:-len(ext)]
            name = stem #  .replace('.', '_')
            full_name = str(rel_path.with_name(name)).replace('/', '.')
        else:
            log.error(f"Source file name should end with %r: %s", ext, path)
            continue
        log.info("Construct resources for: %s @ %s", full_name, hyperapp_dir)
        resource_module = services.construct_resources(full_name, name, abs_path, hyperapp_dir)
        # res_path = path.with_name(stem + '.resources.yaml')
        # resource_module.save_as(res_path)
        # log.info("Written resource file: %s", res_path)
