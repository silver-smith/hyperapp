from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .command_hub import CommandHub
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'name')


class LayoutKeyList(SimpleListObject):

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

    def get_title(self):
        return f"Layout keys for: {self._object.get_title()}"

    @property
    def data(self):
        return htypes.layout_key_list.layout_key_list(self._piece_ref)

    def get_columns(self):
        return [
            Column('name', is_key=True),
            ]

    async def get_all_items(self):
        return [
            Item('origin'),
            Item('destination'),
            ]

    @property
    def _piece_ref(self):
        return self._ref_registry.register_object(self._object.data)
        
    @command('open', kind='element')
    async def open(self, item_key):
        if item_key == 'destination':
            return htypes.category_list.category_list(self._piece_ref)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.layout_key_list.layout_key_list,
            LayoutKeyList.from_state,
            services.ref_registry,
            services.async_ref_resolver,
            services.object_registry,
            services.object_layout_association,
            services.object_layout_producer,
            )
