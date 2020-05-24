from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .chooser import Chooser
from .column import Column
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'id')


class LayoutRefField:
    pass


class ViewChooser(SimpleListObject, Chooser):

    @classmethod
    def from_state(cls, state, available_object_layouts):
        return cls(available_object_layouts)

    def __init__(self, available_object_layouts):
        SimpleListObject.__init__(self)
        Chooser.__init__(self)
        self._available_object_layouts = available_object_layouts
        self._category = 'list'  # todo: do not use params editor to choose layout

    def get_title(self):
        return 'Choose view'

    @property
    def data(self):
        return htypes.view_chooser.view_chooser()

    def get_columns(self):
        return [
            Column('id', is_key=True),
            ]

    async def get_all_items(self):
        return [Item(name) for name in self._available_object_layouts.category_name_list(self._category)]

    def get_value(self):
        return None

    @command('choose', kind='element')
    async def _choose(self, item_key):
        layout_ref = self._available_object_layouts.get_layout_ref(self._category, name=item_key)
        return (await self.chooser_call_callback(layout_ref))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.field_types[LayoutRefField] = htypes.view_chooser.view_chooser()
        services.object_registry.register_type(
            htypes.view_chooser.view_chooser, ViewChooser.from_state, services.available_object_layouts)
