from hyperapp.client.module import ClientModule
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry = object_registry = AsyncCapsuleRegistry('object', services.type_resolver)
        services.object_resolver = object_resolver = AsyncCapsuleResolver(services.async_ref_resolver, object_registry)
