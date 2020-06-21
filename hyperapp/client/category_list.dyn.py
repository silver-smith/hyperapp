from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'category layout')


class CategoryList(SimpleListObject):

    @classmethod
    async def from_state(cls, state, ref_registry, async_ref_resolver, object_registry, object_layout_association):
        piece = await async_ref_resolver.resolve_ref_to_object(state.piece_ref)
        object = await object_registry.resolve_async(piece)
        return cls(ref_registry, async_ref_resolver, object_layout_association, object)

    def __init__(self, ref_registry, async_ref_resolver, object_layout_association, object):
        super().__init__()
        self._ref_registry = ref_registry
        self._async_ref_resolver = async_ref_resolver
        self._object_layout_association = object_layout_association
        self._object = object

    def get_title(self):
        return f"Categories for: {self._object.get_title()}"

    @property
    def data(self):
        return htypes.category_list.category_list(self._piece_ref)

    def get_columns(self):
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

    @command('open', kind='element')
    def open(self, item_key):
        return htypes.layout_editor.object_layout_editor(self._piece_ref, category=item_key)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.category_list.category_list, CategoryList.from_state,
            services.ref_registry, services.async_ref_resolver, services.object_registry, services.object_layout_association)
