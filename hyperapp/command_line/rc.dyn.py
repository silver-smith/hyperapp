import logging

log = logging.getLogger(__name__)

from .services import (
    mosaic,
    resource_registry,
    )


def compile_resources(rc_res, subdir_list, root_dirs, module_list, rpc_timeout):
    generator_ref = mosaic.put(rc_res)
    log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)
    services.compile_resources(generator_ref, subdir_list, root_dirs, module_list, rpc_timeout)
