import abc

from hyperapp.client.module import ClientModule
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver


class LayoutViewProducer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def produce_view(self, type_ref, object, observer):
        pass


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.layout_registry = layout_registry = AsyncCapsuleRegistry('layout', services.type_resolver)
        services.layout_resolver = layout_resolver = AsyncCapsuleResolver(services.async_ref_resolver, layout_registry)
