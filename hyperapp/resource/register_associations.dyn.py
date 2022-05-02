import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


def register_associations(meta_registry, resource_module_registry):
    for resource_module in resource_module_registry.values():
        for assoc in resource_module.associations:
            log.info("Register association: %r", assoc)
            meta_registry.animate(assoc)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        register_associations(services.meta_registry, services.resource_module_registry)
