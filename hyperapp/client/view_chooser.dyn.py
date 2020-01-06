from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'id')


class ViewFieldRef:
    pass


class ViewChooser(SimpleListObject):

    @classmethod
    def from_state(cls, state, available_view_registry):
        return cls(available_view_registry)

    def __init__(self, available_view_registry):
        super().__init__()
        self._available_view_registry = available_view_registry

    def get_title(self):
        return 'Choose view'

    def get_columns(self):
        return [
            Column('id', is_key=True),
            ]

    async def get_all_items(self):
        return [Item(id) for id in self._available_view_registry]

    @command('choose', kind='element')
    def _choose(self, item_key):
        assert 0  # todo


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.field_types[ViewFieldRef] = htypes.view_chooser.view_chooser()
        services.object_registry.register_type(htypes.view_chooser.view_chooser, ViewChooser.from_state, services.available_view_registry)
