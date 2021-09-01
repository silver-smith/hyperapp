# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

from . import htypes
from .command import command
from .view_command import ViewCommander

_log = logging.getLogger(__name__)


_HistoryItem = namedtuple('_HistoryItem', 'piece origin_dir view_state')


class Command:

    def __init__(self, name, dir, fn, kind):
        self.name = name
        self.dir = dir
        self._fn = fn
        self.kind = kind

    async def run(self):
        return await self._fn()


class _History:

    def __init__(self):
        self._backward_piece_list = []  # last element is current piece
        self._forward_piece_list = []

    @property
    def current_piece(self):
        return self._backward_piece_list[-1]

    def append(self, piece):
        self._backward_piece_list.append(piece)
        self._forward_piece_list.clear()

    def move_backward(self):
        # Move current piece to forward list and return previous one
        current_piece = self._backward_piece_list.pop()
        self._forward_piece_list.append(current_piece)
        return self._backward_piece_list[-1]

    def move_forward(self):
        piece = self._forward_piece_list.pop()
        self._backward_piece_list.append(piece)
        return piece


class Navigator(ViewCommander):

    @classmethod
    async def from_state(
            cls,
            state,
            command_hub,
            mosaic,
            async_web,
            object_factory,
            object_commands_factory,
            view_producer,
            global_command_list,
            ):
        self = cls(
            mosaic,
            object_factory,
            object_commands_factory,
            view_producer,
            global_command_list,
            # path,
            command_hub,
            )
        await self._async_init(async_web, state.current_piece_ref, state.origin_dir)
        return self

    def __init__(
            self,
            mosaic,
            object_factory,
            object_commands_factory,
            view_producer,
            global_command_list,
            # path,
            command_hub,
            ):
        super().__init__()
        self._mosaic = mosaic
        self._object_factory = object_factory
        self._object_commands_factory = object_commands_factory
        self._view_producer = view_producer
        self._global_command_list = global_command_list
        self._command_hub = command_hub
        self._history = _History()
        self._current_object = None
        self._current_origin_dir = None
        self._current_view = None

    async def _async_init(self, async_web, initial_piece_ref, origin_dir):
        piece = await async_web.summon(initial_piece_ref)
        self._current_object = object = await self._object_factory.animate(piece)
        self._current_origin_dir = [
            await async_web.summon(ref)
            for ref in origin_dir
            ]
        view = await self._create_view(self._current_object, self._current_origin_dir)
        self._history.append(_HistoryItem(self._current_object.piece, self._current_origin_dir, view.piece))
        self._current_view = view

    @property
    def state(self):
        piece_ref = self._mosaic.put(self._current_object.piece)
        origin_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in self._current_origin_dir
            )
        return htypes.navigator.navigator(piece_ref, origin_dir_refs)

    @property
    def qt_widget(self):
        return self._current_view

    def ensure_has_focus(self):
        self._current_view.setFocus()

    @property
    def title(self):
        return self._current_object.title

    def iter_view_commands(self):
        for command in self.get_command_list():
            yield (['navigator'], command)

    async def get_current_commands(self):
        object_command_list = await self._object_commands_factory.get_object_command_list(self._current_view.object)
        object_view_command_list = [
            Command(command.name, command.dir, partial(self._run_object_command, command), kind='object')
            for command in object_command_list
            ]
        global_command_list = [
            Command(command.name, command.dir, partial(self._run_global_command, command), kind='global')
            for command in self._global_command_list
            ]
        return [
            *super().get_command_list(),
            *object_view_command_list,
            *global_command_list,
            ]

    def _origin_dir(self, object, command_dir):
        command_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in command_dir
            )
        return [htypes.view.command_source_d(command_dir_refs), *object.dir_list[-1]]

    async def _run_object_command(self, command):
        view_state = self._current_view.state
        _log.info("Run object command: %s with state %s, origin %s", command, view_state, self._current_origin_dir)
        piece = await command.run(self._current_view.object, view_state, self._current_origin_dir)
        _log.info("Run object command %s result: %r", command, piece)
        if piece is None:
            return
        await self._open_piece_and_save_history(piece, command.dir)

    async def _run_global_command(self, command):
        _log.info("Run global command: %s", command)
        piece = await command.run()
        _log.info("Run global command %s result: %r", command, piece)
        if piece is None:
            return
        await self._open_piece_and_save_history(piece, command.dir)

    async def _open_piece_and_save_history(self, piece, command_dir):
        object = await self._object_factory.animate(piece)
        origin_dir = self._origin_dir(object, command_dir)
        await self._open_object(object, origin_dir)
        self._history.append(_HistoryItem(self._current_object.piece, self._current_origin_dir, self._current_view.piece))

    async def _open_object(self, object, origin_dir):
        view = await self._create_view(object, origin_dir)
        self._current_object = object
        self._current_origin_dir = origin_dir
        owner = self._current_view.parent().parent()  # Assuming parent is tab view; todo: unhack.
        self._current_view = view
        owner.replace_qt_widget(self)
        await self._command_hub.update()

    async def _create_view(self, object, origin_dir):
        return await self._view_producer.create_view(object, add_dir_list=[origin_dir])

    @command
    async def go_backward(self):
        try:
            item = self._history.move_backward()
        except IndexError:
            return
        object = await self._object_factory.animate(item.piece)
        await self._open_object(object, item.origin_dir)

    @command
    async def go_forward(self):
        try:
            item = self._history.move_forward()
        except IndexError:
            return
        object = await self._object_factory.animate(item.piece)
        await self._open_object(object, item.origin_dir)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_registry.register_actor(
            htypes.navigator.navigator,
            Navigator.from_state,
            services.mosaic,
            services.async_web,
            services.object_factory,
            services.object_commands_factory,
            services.view_producer,
            services.global_command_list,
            )
