from collections import namedtuple

from hyperapp.common.ref import ref_repr

from . import htypes
from .object_command import command
from .column import Column
from .simple_list_object import SimpleListObject
from .module import ClientModule


Item = namedtuple('Item', 'id name')


class ParamsEditorSample(SimpleListObject):

    @classmethod
    def from_state(cls, state):
        return cls()

    @property
    def title(self):
        return 'Param editor samples'

    @property
    def piece(self):
        return htypes.params_editor_sample.params_editor_sample()

    @property
    def columns(self):
        return [
            Column('id', is_key=True),
            Column('name'),
            ]

    async def get_all_items(self):
        return [
            Item('single_simple_str', 'Single simple str'),
            Item('two_simple_strings', 'Two simple strings'),
            ]

    def get_item_command_list(self, item_key):
        command_map = dict(
            single_simple_str=self._test_single_simple_str,
            two_simple_strings=self._test_two_simple_str,
            )
        try:
            return [command_map[item_key]]
        except KeyError:
            return []

    @command('test_single_simple_str', kind='element')
    def _test_single_simple_str(self, item_key, str_param: str):
        text = f"Opened item {item_key}: {str_param!r}"
        return text

    @command('test_two_simple_str', kind='element')
    def _test_two_simple_str(self, item_key, str_param_1: str, str_param_2: str):
        text = f"Opened item {item_key}: {str_param_1!r},  {str_param_2!r}"
        return text



class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        services.object_registry.register_actor(htypes.params_editor_sample.params_editor_sample, ParamsEditorSample.from_state)

    @command('open_params_editor_sample')
    async def open_params_editor_sample(self):
        return htypes.params_editor_sample.params_editor_sample()
