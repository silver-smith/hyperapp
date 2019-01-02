import logging

from hyperapp.common.module import Module
from hyperapp.common.capsule_registry import CapsuleRegistry, CapsuleResolver

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.registry'


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.transport_registry = transport_registry = CapsuleRegistry('transport', services.type_resolver)
        services.transport_resolver = CapsuleResolver(services.ref_resolver, transport_registry)
        services.local_transport_ref_set = set()
