import logging

from .capsule_registry import CapsuleRegistry, CapsuleResolver
from .module import ClientModule


MODULE_NAME = 'async_ref_resolver'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.handle_registry = handle_registry = CapsuleRegistry('handle', services.types)
        services.handle_resolver = CapsuleResolver(services.async_ref_resolver, handle_registry)
