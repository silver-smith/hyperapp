from hyperapp.client.module import ClientModule

from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_type_codereg = AsyncCapsuleRegistry('object_type', services.type_resolver)
        services.object_type_resolver = AsyncCapsuleResolver(services.async_ref_resolver, services.object_type_codereg)
