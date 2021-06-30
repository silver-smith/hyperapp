# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

from . import htypes
from .command import command
from .layout import GlobalLayout

_log = logging.getLogger(__name__)


_HistoryItem = namedtuple('_HistoryItem', 'piece view_state')


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


class NavigatorLayout(GlobalLayout):

    @classmethod
    async def from_data(
            cls,
            state,
            path,
            command_hub,
            view_opener,
            mosaic,
            async_web,
            object_animator,
            object_commands_factory,
            view_factory,
            global_command_list,
            ):
        self = cls(
            mosaic,
            object_animator,
            object_commands_factory,
            view_factory,
            global_command_list,
            path,
            command_hub,
            view_opener,
            )
        await self._async_init(async_web, state.current_piece_ref)
        return self

    def __init__(
            self,
            mosaic,
            object_animator,
            object_commands_factory,
            view_factory,
            global_command_list,
            path,
            command_hub,
            view_opener,
            ):
        super().__init__(path)
        self._mosaic = mosaic
        self._object_animator = object_animator
        self._object_commands_factory = object_commands_factory
        self._view_factory = view_factory
        self._global_command_list = global_command_list
        self._command_hub = command_hub
        self._view_opener = view_opener
        self._history = _History()
        self._current_object = None
        self._current_layout_handle = None
        self._current_view = None

    async def _async_init(self, async_web, initial_piece_ref):
        piece = await async_web.summon(initial_piece_ref)
        self._current_object = object = await self._object_animator.animate(piece)

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._current_object.piece)
        return htypes.navigator.navigator(piece_ref)

    async def create_view(self):
        self._current_view = await self._create_view(self._current_object)
        self._history.append(_HistoryItem(self._current_object.piece, self._current_view.piece))
        return self._current_view

    async def visual_item(self):
        piece = self._current_object.piece
        return self.make_visual_item('Navigator', children=[
            self.make_visual_item(str(piece), name='current'),
            ])

    async def get_current_commands(self):
        object_command_list = await self._object_commands_factory.get_object_command_list(self._current_object)
        object_view_command_list = [
            Command(command.name, command.dir, partial(self._run_object_command, command), kind='object')
            for command in object_command_list
            ]
        global_command_list = [
            Command(command.name, command.dir, partial(self._run_global_command, command), kind='global')
            for command in self._global_command_list
            ]
        return [
            *await super().get_current_commands(),
            *object_view_command_list,
            *global_command_list,
            ]

    async def _create_view(self, object):
        return await self._view_factory.create_view(object)

    async def _run_object_command(self, command):
        view_state = self._current_view.state
        _log.info("Run object command: %s with state %s", command, view_state)
        piece = await command.run(self._current_object, view_state)
        _log.info("Run object command %s result: %r", command, piece)
        if piece is None:
            return
        await self._open_piece(piece)

    async def _run_global_command(self, command):
        _log.info("Run global command: %s", command)
        piece = await command.run()
        _log.info("Run global command %s result: %r", command, piece)
        if piece is None:
            return
        await self._open_piece(piece)

    async def _open_piece(self, piece):
        await self._open_piece_impl(piece)
        self._history.append(_HistoryItem(self._current_object.piece, self._current_view.piece))

    async def _open_piece_impl(self, piece):
        self._current_object = await self._object_animator.animate(piece)
        self._current_view = await self._create_view(self._current_object)
        self._view_opener.open(self._current_view)
        await self._command_hub.update()

    @command
    async def go_backward(self):
        try:
            item = self._history.move_backward()
        except IndexError:
            return
        await self._open_piece_impl(item.piece)

    @command
    async def go_forward(self):
        try:
            item = self._history.move_forward()
        except IndexError:
            return
        await self._open_piece_impl(item.piece)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_registry.register_actor(
            htypes.navigator.navigator,
            NavigatorLayout.from_data,
            services.mosaic,
            services.async_web,
            services.object_animator,
            services.object_commands_factory,
            services.view_factory,
            services.global_command_list,
            )
