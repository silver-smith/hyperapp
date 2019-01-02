import logging

from hyperapp.client.module import ClientModule
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.registry'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.transport_registry = transport_registry = AsyncCapsuleRegistry('transport', services.types)
        services.transport_resolver = AsyncCapsuleResolver(services.async_ref_resolver, transport_registry)
