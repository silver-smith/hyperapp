import logging

from hyperapp.common.module import Module
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver


MODULE_NAME = 'async_ref_resolver'


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.handle_registry = handle_registry = AsyncCapsuleRegistry('handle', services.type_resolver)
        services.handle_resolver = AsyncCapsuleResolver(services.async_ref_resolver, handle_registry)
