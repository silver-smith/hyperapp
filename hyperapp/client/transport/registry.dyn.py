import logging

from ..capsule_registry import CapsuleRegistry, CapsuleResolver
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.registry'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.transport_registry = transport_registry = CapsuleRegistry('transport', services.types)
        services.transport_resolver = CapsuleResolver(services.async_ref_resolver, transport_registry)
