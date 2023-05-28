import logging

log = logging.getLogger(__name__)

from .services import (
    mosaic,
    resource_registry,
    )


def update_resources(update_resources_res, subdir_list, root_dirs, module_list, rpc_timeout):
    generator_ref = mosaic.put(update_resources_res)
    log.info("Update resources at: %s, %s: %s", subdir_list, root_dirs, module_list)
    services.update_resources(generator_ref, subdir_list, root_dirs, module_list, rpc_timeout)
