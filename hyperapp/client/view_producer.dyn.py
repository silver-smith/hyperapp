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

    async def produce_view(self, state, object, observer=None):
        type_ref = self._state_type_ref(state)
        resource_key = resource_key_t(type_ref, ['layout'])
        layout = self._resource_resolver.resolve(resource_key, LOCALE)
        if layout:
            producer = self._layout_registry.resolve(layout)
            _log.info("Producing view for %s %r with %s using %s", ref_repr(type_ref), state, layout, producer)
            return (await producer.produce_view(type_ref, object, observer))
        return (await self._view_producer_registry.produce_view(type_ref, object, observer))

    def _state_type_ref(self, state):
        current_t = deduce_value_type(state)
        return self._type_resolver.reverse_resolve(current_t)


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
