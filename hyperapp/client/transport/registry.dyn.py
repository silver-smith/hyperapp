import logging

from hyperapp.client.module import ClientModule
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver

log = logging.getLogger(__name__)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.transport_registry = transport_registry = AsyncCapsuleRegistry('transport', services.type_resolver)
        services.transport_resolver = AsyncCapsuleResolver(services.async_ref_resolver, transport_registry)
