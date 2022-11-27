import logging
from functools import partial

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


def register_associations(meta_registry, resource_registry):
    for assoc in reversed(resource_registry.associations):
        log.info("Register association: %r", assoc)
        meta_registry.animate(assoc)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.register_associations = partial(register_associations, services.meta_registry)
