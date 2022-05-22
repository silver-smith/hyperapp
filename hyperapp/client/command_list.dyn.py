
from . import htypes


class _CommandList:

    def __init__(self, lcs):
        self._lcs = lcs

    def _command_shortcut(self, dir):
        return self._lcs.get([dir, htypes.command.command_shortcut_d()])


class GlobalCommandList(_CommandList):

    def __init__(self, piece, lcs, python_object_creg, global_command_list):
        super().__init__(lcs)
        self._python_object_creg = python_object_creg
        self._global_command_list = global_command_list

    def get(self):
        record_list = []
        for command in self._global_command_list:
            dir = self._python_object_creg.invite(command.dir)
            item = htypes.command_list.item(
                name=dir._t.name.rstrip('_d'),  # todo: load title from lcs.
                shortcut=self._command_shortcut(dir) or '',
                )
            record_list.append(item)
        return record_list


class ViewCommandList(_CommandList):

    def __init__(self, piece, lcs, python_object_creg, root_view):
        super().__init__(lcs)
        self._python_object_creg = python_object_creg
        self._root_view = root_view

    # todo: postpone population; empty list is shown if this is initially opened object.
    def get(self):
        record_list = []
        for path, command in self._root_view.iter_view_commands():
            [dir] = command.dir
            item = htypes.command_list.view_item(
                name=command.name,
                path='/'.join(path),
                shortcut=self._command_shortcut(dir) or '',
                )
            record_list.append(item)
        return record_list


def open_global_command_list():
    return htypes.command_list.global_command_list()


def open_view_command_list():
    return htypes.command_list.view_command_list()
