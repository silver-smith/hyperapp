import logging

from . import htypes
from .services import (
    adapter_factory,
    global_command_list,
    lcs,
    mosaic,
    object_commands_factory,
    python_object_creg,
    root_view,
    web,
    )
from .qt_keys import run_input_key_dialog

_log = logging.getLogger(__name__)


class _CommandList:

    def _command_shortcut(self, dir):
        return lcs.get([dir, htypes.command.command_shortcut_d()])

    def set_key(self, current_item):
        shortcut = run_input_key_dialog()
        if shortcut:
            self._set_key(current_item, shortcut)

    def set_key_escape(self, current_item):
        self._set_key(current_item, 'Escape')

    def _set_key(self, item, shortcut):
        _log.info("Set shortcut for command %s: %r", item.name, shortcut)
        dir = web.summon(item.dir)
        lcs.set([dir, htypes.command.command_shortcut_d()], shortcut, persist=True)


class GlobalCommandList(_CommandList):

    def __init__(self, piece):
        pass

    def get(self):
        record_list = []
        for command in global_command_list:
            dir = python_object_creg.invite(command.dir)
            item = htypes.command_list.item(
                name=dir._t.name.rstrip('_d'),  # todo: load title from lcs.
                dir=mosaic.put(dir),
                shortcut=self._command_shortcut(dir) or '',
                )
            record_list.append(item)
        return record_list


class ViewCommandList(_CommandList):

    def __init__(self, piece):
        pass

    # todo: postpone population; empty list is shown if this is initially opened object.
    def get(self):
        record_list = []
        for path, command in root_view.iter_view_commands():
            dir = command.dir
            item = htypes.command_list.view_item(
                name=command.name,
                dir=mosaic.put(dir),
                path='/'.join(path),
                shortcut=self._command_shortcut(dir) or '',
                )
            record_list.append(item)
        return record_list


class ObjectCommandList(_CommandList):

    def __init__(self, piece):
        self._object_piece = web.summon(piece.piece_ref)
        self._view_state = web.summon(piece.view_state_ref)

    async def get(self):
        adapter = await adapter_factory(self._object_piece)
        record_list = []
        for piece in object_commands_factory.enum_object_command_pieces(adapter):
            dir = python_object_creg.invite(piece.dir)
            item = htypes.command_list.item(
                name=dir._t.name.rstrip('_d'),  # todo: load title from lcs.
                dir=mosaic.put(dir),
                shortcut=self._command_shortcut(dir) or '',
                )
            record_list.append(item)
        return record_list


def open_global_command_list():
    return htypes.command_list.global_command_list()


def open_view_command_list():
    return htypes.command_list.view_command_list()


def object_commands(piece, view_state):
    return htypes.command_list.object_command_list(
        piece_ref=mosaic.put(piece),
        view_state_ref=mosaic.put(view_state),
        )
