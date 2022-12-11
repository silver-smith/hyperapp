import logging
from functools import partial

from . import htypes
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


def register_associations(meta_registry, resource_registry):
    for assoc in resource_registry.associations:
        if isinstance(assoc, htypes.meta_registry.meta_association):
            log.info("Register meta association: %r", assoc)
            meta_registry.animate(assoc)
    for assoc in resource_registry.associations:
        if not isinstance(assoc, htypes.meta_registry.meta_association):
            log.info("Register association: %r", assoc)
            meta_registry.animate(assoc)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.register_associations = partial(register_associations, services.meta_registry)
