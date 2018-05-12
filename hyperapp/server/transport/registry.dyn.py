import logging

from ..registry import CapsuleRegistry, CapsuleResolver
from ..module import ServerModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.registry'


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.transport_registry = transport_registry = CapsuleRegistry('transport', services.types)
        services.transport_resolver = CapsuleResolver(services.ref_resolver, transport_registry)
