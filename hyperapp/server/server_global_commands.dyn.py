from functools import cached_property

from hyperapp.common.code_registry import CodeRegistry

from . import htypes
from .services import (
    global_command_list,
    python_object_creg,
    types,
    web,
    )


class ServerGlobalCommands:

    def __init__(self, piece):
      pass

    @cached_property
    def _items(self):
        item_list = []
        for command in global_command_list:
            item = server_command_creg.animate(command)
            item_list.append(item)
        return item_list

    def get(self):
        return self._items

    def run(self, current_key):
        name_to_fn = {item.name: item.function for item in self._items}
        fn_ref = name_to_fn[current_key]
        fn = python_object_creg.invite(fn_ref)
        return fn()


def global_command_to_item(piece):
    dir = python_object_creg.invite(piece.dir)
    assert dir._t.name.endswith('_d')
    return htypes.server_global_commands.item(
        name=dir._t.name[:-2],  # todo: load title from lcs.
        function=piece.function,
        )


server_command_creg = CodeRegistry('server_command', web, types)
server_command_creg.register_actor(htypes.impl.global_command_impl, global_command_to_item)
