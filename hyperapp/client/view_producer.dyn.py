import logging

from hyperapp.common.htypes import resource_key_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import ref_repr
from hyperapp.client.module import ClientModule
from .layout_registry import LayoutViewProducer

_log = logging.getLogger(__name__)

LOCALE = 'en'


class ViewProducer(LayoutViewProducer):

    def __init__(self, type_resolver, resource_resolver, object_registry, view_producer_registry, layout_registry):
        self._type_resolver = type_resolver
        self._resource_resolver = resource_resolver
        self._object_registry = object_registry
        self._view_producer_registry = view_producer_registry
        self._layout_registry = layout_registry

    async def produce_view(self, piece, object, observer=None):
        type_ref = self._piece_type_ref(piece)
        resource_key = resource_key_t(type_ref, ['layout'])
        layout = self._resource_resolver.resolve(resource_key, LOCALE)
        if layout:
            producer = self._layout_registry.resolve(layout)
            _log.info("Producing view for %s %r with %s using %s", ref_repr(type_ref), piece, layout, producer)
            return (await producer.produce_view(piece, object, observer))
        return (await self.produce_default_view(piece, object, observer))

    async def produce_default_view(self, piece, object, observer=None):
        return (await self._view_producer_registry.produce_view(piece, object, observer))

    def _piece_type_ref(self, piece):
        t = deduce_value_type(piece)
        return self._type_resolver.reverse_resolve(t)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_producer = ViewProducer(
            services.type_resolver,
            services.resource_resolver,
            services.object_registry,
            services.view_producer_registry,
            services.layout_registry,
            )
