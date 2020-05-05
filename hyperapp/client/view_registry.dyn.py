import logging

from hyperapp.client.module import ClientModule

from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver

_log = logging.getLogger(__name__)


class NotApplicable(Exception):

    def __init__(self, object):
        super().__init__("This view producer is not applicable for object {}".format(object))


class ViewProducerRegistry:

    def __init__(self, object_layout_overrides, object_layout_resolver):
        self._object_layout_overrides = object_layout_overrides
        self._object_layout_resolver = object_layout_resolver
        self._producer_list = []

    def register_view_producer(self, producer):
        self._producer_list.append(producer)

    async def produce_layout(self, piece, object, command_hub, piece_opener):
        try:
            layout_ref = self._object_layout_overrides[object.hashable_resource_key]
        except KeyError:
            return (await self._produce_default_layout(piece, object, command_hub, piece_opener))
        else:
            return (await self._object_layout_resolver.resolve(layout_ref, piece, object, command_hub, piece_opener))

    async def _produce_default_layout(piece, object, command_hub, piece_opener):
        for producer in self._producer_list:
            try:
                return (await producer(piece, object, command_hub, piece_opener))
            except NotApplicable:
                pass
        raise RuntimeError("No view is known to support object {}".format(object))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_layout_overrides = {}  # resource key -> layout ref
        services.available_view_registry = {}  # id -> view ref, views available to add to layout
        services.view_registry = view_registry = AsyncCapsuleRegistry('view', services.type_resolver)
        services.view_resolver = view_resolver = AsyncCapsuleResolver(services.async_ref_resolver, view_registry)
        services.object_layout_registry = AsyncCapsuleRegistry('object_layout', services.type_resolver)
        services.object_layout_resolver = AsyncCapsuleResolver(services.async_ref_resolver, services.object_layout_registry)
        services.object_layout_list = []
        services.view_producer_registry = ViewProducerRegistry(services.object_layout_overrides, services.object_layout_resolver)
