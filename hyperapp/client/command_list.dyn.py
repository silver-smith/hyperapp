
from . import htypes


class GlobalCommandList:

    def __init__(self, piece, lcs, python_object_creg, global_command_list):
        self._lcs = lcs
        self._python_object_creg = python_object_creg
        self._global_command_list = global_command_list

    def get(self):
        record_list = []
        for command in self._global_command_list:
            dir = self._python_object_creg.invite(command.dir)
            item = htypes.command_list.item(
                name=dir._t.name.rstrip('_d'),  # todo: load title from lcs.
                shortcut=self._command_shortcut(command) or '',
                )
            record_list.append(item)
        return record_list

    def _command_shortcut(self, command):
        return self._lcs.get([*command.dir, htypes.command.command_shortcut_d()])


def open_global_command_list():
    return htypes.command_list.global_command_list()
