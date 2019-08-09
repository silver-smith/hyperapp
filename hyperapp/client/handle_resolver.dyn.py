import logging

from hyperapp.common.module import Module
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        services.handle_registry = handle_registry = AsyncCapsuleRegistry('handle', services.type_resolver)
        services.handle_resolver = AsyncCapsuleResolver(services.async_ref_resolver, handle_registry)
