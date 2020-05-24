from collections import namedtuple

from hyperapp.common.ref import ref_repr
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .simple_list_object import SimpleListObject
from .view_chooser import LayoutRefField


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

    @command('test_single_simple_str', kind='element')
    def _test_single_simple_str(self, item_key, str_param: str):
        text = f"Opened item {item_key}: {str_param!r}"
        return htypes.text.text(text)

    @command('test_two_simple_str', kind='element')
    def _test_two_simple_str(self, item_key, str_param_1: str, str_param_2: str):
        text = f"Opened item {item_key}: {str_param_1!r},  {str_param_2!r}"
        return htypes.text.text(text)

    # todo: remove optionality when predefined params are supported by param editor
    @command('test_view_chooser', kind='element')
    def _test_view_chooser(self, item_key, view: LayoutRefField):
        text = f"Opened item {item_key}: {ref_repr(view)}"
        return htypes.text.text(text)



class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(htypes.params_editor_sample.params_editor_sample, SampleList.from_state)

    @command('open_params_editor_sample')
    async def open_params_editor_sample(self):
        return htypes.params_editor_sample.params_editor_sample()
