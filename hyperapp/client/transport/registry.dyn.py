import logging

from ..referred_registry import ReferredRegistry, ReferredResolver
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.registry'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.transport_registry = transport_registry = ReferredRegistry('transport', services.type_registry_registry)
        services.transport_resolver = ReferredResolver(services.async_ref_resolver, transport_registry)
