import logging

log = logging.getLogger(__name__)

from .services import (
    resource_registry,
    register_associations,
    )
from . import meta_registry_association


def update_resources(root_dir, resource_dir_list, source_dir_list):
    meta_registry_association.init()
    register_associations(resource_registry)
    log.info("Update resources at: %s", source_dir_list)
    services.update_resources(root_dir, resource_dir_list, source_dir_list)
