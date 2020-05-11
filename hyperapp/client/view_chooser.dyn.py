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
    def from_state(cls, state, object_layout_registry):
        return cls(object_layout_registry)

    def __init__(self, object_layout_registry):
        SimpleListObject.__init__(self)
        Chooser.__init__(self)
        self._object_layout_registry = object_layout_registry

    def get_title(self):
        return 'Choose view'

    def get_columns(self):
        return [
            Column('id', is_key=True),
            ]

    async def get_all_items(self):
        return [Item(name) for name in self._object_layout_registry.category_name_list(category)]  # todo: category

    def get_value(self):
        return None

    @command('choose', kind='element')
    async def _choose(self, item_key):
        assert len(self._object_layout_registry) == 1  # todo: proper get_all_items method
        [ref] = self._object_layout_registry
        return (await self.chooser_call_callback(ref))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.field_types[ViewFieldRef] = htypes.view_chooser.view_chooser()
        services.object_registry.register_type(
            htypes.view_chooser.view_chooser, ViewChooser.from_state, services.object_layout_registry)
