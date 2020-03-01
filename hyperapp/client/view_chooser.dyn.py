from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .chooser import Chooser
from .column import Column
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'id')


class ViewFieldRef:
    pass


class ViewChooser(SimpleListObject, Chooser):

    @classmethod
    def from_state(cls, state, available_view_registry):
        return cls(available_view_registry)

    def __init__(self, available_view_registry):
        SimpleListObject.__init__(self)
        Chooser.__init__(self)
        self._available_view_registry = available_view_registry

    def get_title(self):
        return 'Choose view'

    def get_columns(self):
        return [
            Column('id', is_key=True),
            ]

    async def get_all_items(self):
        return [Item(id) for id in self._available_view_registry]

    def get_value(self):
        return None

    @command('choose', kind='element')
    async def _choose(self, item_key):
        view_ref = self._available_view_registry[item_key]
        return (await self.chooser_call_callback(view_ref))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.field_types[ViewFieldRef] = htypes.view_chooser.view_chooser()
        services.object_registry.register_type(htypes.view_chooser.view_chooser, ViewChooser.from_state, services.available_view_registry)
