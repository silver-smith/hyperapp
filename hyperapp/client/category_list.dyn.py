from collections import namedtuple

from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .column import Column
from .command_hub import CommandHub
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'category layout')


class CategoryList(SimpleListObject):

    @classmethod
    async def from_state(cls, state, ref_registry, async_ref_resolver, object_registry, object_layout_association, object_layout_producer):
        piece = await async_ref_resolver.resolve_ref_to_object(state.piece_ref)
        object = await object_registry.resolve_async(piece)
        return cls(ref_registry, async_ref_resolver, object_layout_association, object_layout_producer, object)

    def __init__(self, ref_registry, async_ref_resolver, object_layout_association, object_layout_producer, object):
        super().__init__()
        self._ref_registry = ref_registry
        self._async_ref_resolver = async_ref_resolver
        self._object_layout_association = object_layout_association
        self._object_layout_producer = object_layout_producer
        self._object = object

    @property
    def title(self):
        return f"Categories for: {self._object.title}"

    @property
    def data(self):
        return htypes.category_list.category_list(self._piece_ref)

    @property
    def columns(self):
        return [
            Column('category', is_key=True),
            Column('layout')
            ]

    async def get_all_items(self):
        return [
            Item(category, await self._category_to_layout(category))
            for category
            in self._object.category_list
            ]

    @property
    def _piece_ref(self):
        return self._ref_registry.register_object(self._object.data)

    async def _category_to_layout(self, category):
        layout_ref = self._object_layout_association.get(category)
        if not layout_ref:
            return None
        return await self._async_ref_resolver.resolve_ref_to_object(layout_ref)

    async def _get_layout_ref(self, category):
        layout_ref = self._object_layout_association.get(category)
        if layout_ref:
            return layout_ref
        layout = await self._object_layout_producer.produce_layout(self._object, layout_watcher=None)
        return self._ref_registry.register_object(layout.data)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.category_list.category_list,
            CategoryList.from_state,
            services.ref_registry,
            services.async_ref_resolver,
            services.object_registry,
            services.object_layout_association,
            services.object_layout_producer,
            )
