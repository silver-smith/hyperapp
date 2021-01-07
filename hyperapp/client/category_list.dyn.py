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
    async def from_state(cls, state, mosaic, async_ref_resolver, object_registry, object_layout_association, object_layout_producer):
        piece = await async_ref_resolver.summon(state.piece_ref)
        object = await object_registry.animate(piece)
        return cls(mosaic, async_ref_resolver, object_layout_association, object_layout_producer, object)

    def __init__(self, mosaic, async_ref_resolver, object_layout_association, object_layout_producer, object):
        super().__init__()
        self._mosaic = mosaic
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
        return self._mosaic.distil(self._object.data)

    async def _category_to_layout(self, category):
        layout_ref = self._object_layout_association.get(category)
        if not layout_ref:
            return None
        return await self._async_ref_resolver.summon(layout_ref)

    async def _get_layout_ref(self, category):
        layout_ref = self._object_layout_association.get(category)
        if layout_ref:
            return layout_ref
        layout = await self._object_layout_producer.produce_layout(self._object, layout_watcher=None)
        return self._mosaic.distil(layout.data)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        # services.object_registry.register_actor(
        #     htypes.category_list.category_list,
        #     CategoryList.from_state,
        #     services.mosaic,
        #     services.async_ref_resolver,
        #     services.object_registry,
        #     services.object_layout_association,
        #     services.object_layout_producer,
        #     )
