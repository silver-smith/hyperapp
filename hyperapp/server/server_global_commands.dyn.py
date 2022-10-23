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

    def get(self):
        item_list = []
        for command in global_command_list:
            item = server_command_creg.animate(command)
            item_list.append(item)
        return item_list

    def run(self, current_item):
        fn = python_object_creg.invite(current_item.function)
        return fn()


def global_command_to_item(piece):
    dir = python_object_creg.invite(piece.dir)
    return htypes.server_global_commands.item(
        name=dir._t.name.rstrip('_d'),  # todo: load title from lcs.
        function=piece.function,
        )


server_command_creg = CodeRegistry('server_command', web, types)
server_command_creg.register_actor(htypes.impl.global_command_impl, global_command_to_item)
