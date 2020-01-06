from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .simple_list_object import SimpleListObject
from .view_chooser import ViewFieldRef


Item = namedtuple('Item', 'id name')


class SampleList(SimpleListObject):

    @classmethod
    def from_state(cls, state):
        return cls()

    def get_title(self):
        return 'Param editor samples'

    def get_columns(self):
        return [
            Column('id', is_key=True),
            Column('name'),
            ]

    async def get_all_items(self):
        return [
            Item('single_simple_str', 'Single simple str'),
            Item('two_simple_strings', 'Two simple strings'),
            Item('view_chooser', 'View chooser'),
            ]

    def get_item_command_list(self, item_key):
        command_map = dict(
            single_simple_str=self._test_single_simple_str,
            two_simple_strings=self._test_two_simple_str,
            view_chooser=self._test_view_chooser,
            )
        try:
            return [command_map[item_key]]
        except KeyError:
            return []

    @command('test_param', kind='element')
    def _test_single_simple_str(self, item_key, str_param: str):
        assert 0  # todo

    @command('test_param', kind='element')
    def _test_two_simple_str(self, item_key, str_param_1: str, str_param_2: str):
        assert 0  # todo

    @command('test_param', kind='element')
    def _test_view_chooser(self, item_key, view: ViewFieldRef):
        assert 0  # todo


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(htypes.params_editor_sample.params_editor_sample, SampleList.from_state)

    @command('open_params_editor_sample')
    async def open_params_editor_sample(self):
        return htypes.params_editor_sample.params_editor_sample()
