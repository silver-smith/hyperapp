import logging

log = logging.getLogger(__name__)

from .services import (
    association_reg,
    mosaic,
    resource_registry,
    )
from . import meta_registry_association


def update_resources(update_resources_res, subdir_list, root_dirs, module_list, rpc_timeout):
    generator_ref = mosaic.put(update_resources_res)
    meta_registry_association.init()
    association_reg.register_association_list(resource_registry.associations)
    log.info("Update resources at: %s, %s: %s", subdir_list, root_dirs, module_list)
    services.update_resources(generator_ref, subdir_list, root_dirs, module_list, rpc_timeout)
