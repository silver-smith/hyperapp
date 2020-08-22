from collections import namedtuple

from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .chooser import Chooser
from .column import Column
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'id categories layout_rec_maker')


class LayoutRecMakerField:
    pass


class ViewChooser(SimpleListObject, Chooser):

    @classmethod
    def from_state(cls, state, available_object_layouts):
        return cls(available_object_layouts, state.category_list)

    def __init__(self, available_object_layouts, category_list):
        SimpleListObject.__init__(self)
        Chooser.__init__(self)
        self._available_object_layouts = available_object_layouts
        self._category_list = category_list
        self._items = [
            Item(rec.name, rec.category_set, rec.layout_rec_maker)
            for rec in self._available_object_layouts.resolve(category_list)
            ]
        self._id_to_item = {item.id: item for item in self._items}

    @property
    def title(self):
        return 'Choose view'

    @property
    def data(self):
        return htypes.view_chooser.view_chooser(self._category_list)

    def get_columns(self):
        return [
            Column('id', is_key=True),
            Column('categories'),
            ]

    async def get_all_items(self):
        return self._items

    def get_value(self):
        return None

    @command('choose', kind='element')
    async def _choose(self, item_key):
        item = self._id_to_item[item_key]
        return (await self.chooser_call_callback(item.layout_rec_maker))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.view_chooser.view_chooser, ViewChooser.from_state, services.available_object_layouts)
