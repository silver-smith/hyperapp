import logging

from . import htypes
from .qt_keys import run_input_key_dialog

_log = logging.getLogger(__name__)


class _CommandList:

    def __init__(self, web, lcs):
        self._web = web
        self._lcs = lcs

    def _command_shortcut(self, dir):
        return self._lcs.get([dir, htypes.command.command_shortcut_d()])

    def set_key(self, current_item):
        shortcut = run_input_key_dialog()
        if shortcut:
            self._set_key(current_item, shortcut)

    def _set_key(self, item, shortcut):
        _log.info("Set shortcut for command %s: %r", item.name, shortcut)
        dir = self._web.summon(item.dir)
        self._lcs.set([dir, htypes.command.command_shortcut_d()], shortcut, persist=True)


class GlobalCommandList(_CommandList):

    def __init__(self, piece, web, lcs, python_object_creg, global_command_list):
        super().__init__(web, lcs)
        self._python_object_creg = python_object_creg
        self._global_command_list = global_command_list

    def get(self):
        record_list = []
        for command in self._global_command_list:
            dir = self._python_object_creg.invite(command.dir)
            item = htypes.command_list.item(
                name=dir._t.name.rstrip('_d'),  # todo: load title from lcs.
                dir=command.dir,
                shortcut=self._command_shortcut(dir) or '',
                )
            record_list.append(item)
        return record_list


class ViewCommandList(_CommandList):

    def __init__(self, piece, web, lcs, mosaic, root_view):
        super().__init__(web, lcs)
        self._mosaic = mosaic
        self._root_view = root_view

    # todo: postpone population; empty list is shown if this is initially opened object.
    def get(self):
        record_list = []
        for path, command in self._root_view.iter_view_commands():
            [dir] = command.dir
            item = htypes.command_list.view_item(
                name=command.name,
                dir=self._mosaic.put(dir),
                path='/'.join(path),
                shortcut=self._command_shortcut(dir) or '',
                )
            record_list.append(item)
        return record_list


def open_global_command_list():
    return htypes.command_list.global_command_list()


def open_view_command_list():
    return htypes.command_list.view_command_list()
