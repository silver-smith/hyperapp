from collections import namedtuple

from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'category')


class CategoryList(SimpleListObject):

    @classmethod
    async def from_state(cls, state, ref_registry, async_ref_resolver, object_registry):
        piece = await async_ref_resolver.resolve_ref_to_object(state.piece_ref)
        object = await object_registry.resolve_async(piece)
        return cls(ref_registry, object)

    def __init__(self, ref_registry, object):
        super().__init__()
        self._ref_registry = ref_registry
        self._object = object

    def get_title(self):
        return f"Categories for: {self._object.get_title()}"

    @property
    def data(self):
        piece_ref = self._ref_registry.register_object(self._object.data)
        return htypes.category_list.category_list(piece_ref)

    def get_columns(self):
        return [
            Column('category', is_key=True),
            ]

    async def get_all_items(self):
        return [Item(category) for category in self._object.category_list]



class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.category_list.category_list, CategoryList.from_state,
            services.ref_registry, services.async_ref_resolver, services.object_registry)
