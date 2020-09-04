from collections import namedtuple

from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .chooser import Chooser
from .column import Column
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'id types layout_data_maker')


class LayoutRecMakerField:
    pass


class ViewChooser(SimpleListObject, Chooser):

    @classmethod
    async def from_state(cls, state, ref_registry, async_ref_resolver, available_object_layouts):
        object_type = await async_ref_resolver.resolve_ref_to_object(state.object_type_ref)
        return cls(ref_registry, available_object_layouts, object_type)

    def __init__(self, ref_registry, available_object_layouts, object_type):
        SimpleListObject.__init__(self)
        Chooser.__init__(self)
        self._ref_registry = ref_registry
        self._available_object_layouts = available_object_layouts
        self._object_type = object_type
        self._items = [
            Item(
                rec.name,
                ', '.join(t.name for t in rec.object_type_t_set),
                rec.layout_data_maker,
                )
            for rec in self._available_object_layouts.resolve(object_type)
            ]
        self._id_to_item = {item.id: item for item in self._items}

    @property
    def title(self):
        return 'Choose view'

    @property
    def data(self):
        object_type_ref = self._ref_registry.register_object(self._object_type)
        return htypes.view_chooser.view_chooser(object_type_ref)

    @property
    def columns(self):
        return [
            Column('id', is_key=True),
            Column('types'),
            ]

    async def get_all_items(self):
        return self._items

    def get_value(self):
        assert False, "ViewChooser.choose command should be used, not ParamsEditor.submit"

    @command('choose', kind='element')
    async def _choose(self, item_key):
        item = self._id_to_item[item_key]
        return (await self.chooser_call_callback(item.layout_data_maker))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.view_chooser.view_chooser, ViewChooser.from_state,
            services.ref_registry, services.async_ref_resolver, services.available_object_layouts)
