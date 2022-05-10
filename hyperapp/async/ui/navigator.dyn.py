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
        self._backward_piece_list = []  # _HistoryItem list
        self._forward_piece_list = []  # _HistoryItem list

    def append(self, item):
        self._backward_piece_list.append(item)
        self._forward_piece_list.clear()

    def move_backward(self, current_item):
        # Move current piece to forward list and return previous one
        prev_item = self._backward_piece_list.pop()
        self._forward_piece_list.append(current_item)
        return prev_item

    def move_forward(self, current_item):
        next_item = self._forward_piece_list.pop()
        self._backward_piece_list.append(current_item)
        return next_item


class Navigator(ViewCommander):

    @classmethod
    async def from_state(
            cls,
            state,
            command_hub,
            mosaic,
            async_web,
            adapter_factory,
            object_commands_factory,
            view_producer,
            global_command_list,
            ):
        self = cls(
            mosaic,
            adapter_factory,
            object_commands_factory,
            view_producer,
            global_command_list,
            # path,
            command_hub,
            )
        await self._async_init(async_web, state.current_piece_ref, state.origin_dir, state.view_state_ref)
        return self

    def __init__(
            self,
            mosaic,
            adapter_factory,
            object_commands_factory,
            view_producer,
            global_command_list,
            # path,
            command_hub,
            ):
        super().__init__()
        self._mosaic = mosaic
        self._adapter_factory = adapter_factory
        self._object_commands_factory = object_commands_factory
        self._view_producer = view_producer
        self._global_command_list = global_command_list
        self._command_hub = command_hub
        self._history = _History()
        self._current_adapter = None
        self._current_piece = None
        self._current_origin_dir = None
        self._current_view = None

    async def _async_init(self, async_web, initial_piece_ref, origin_dir, view_state_ref):
        piece = await async_web.summon(initial_piece_ref)
        self._current_adapter = await self._adapter_factory(piece)
        self._current_piece = piece
        self._current_origin_dir = [
            await async_web.summon(ref)
            for ref in origin_dir
            ]
        view = await self._create_view(self._current_adapter, self._current_origin_dir)
        if view_state_ref is not None:
            view.state = await async_web.summon(view_state_ref)
        self._current_view = view

    @property
    def state(self):
        piece_ref = self._mosaic.put(self._current_piece)
        origin_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in self._current_origin_dir
            )
        view_state = self._current_view.state
        if view_state is not None:
            view_state_ref = self._mosaic.put(view_state)
        else:
            view_state_ref = None
        return htypes.navigator.navigator(piece_ref, origin_dir_refs, view_state_ref)

    @property
    def qt_widget(self):
        return self._current_view

    def ensure_has_focus(self):
        self._current_view.setFocus()

    @property
    def title(self):
        return self._current_adapter.title

    def iter_view_commands(self):
        for command in self.get_command_list():
            yield (['navigator'], command)

    async def get_current_commands(self):
        object_command_list = await self._object_commands_factory.get_object_command_list(
            self, self._current_piece, self._current_adapter, self._current_view)
        return [
            *super().get_command_list(),
            *object_command_list,
            *self._global_command_list,
            ]

    def _origin_dir(self, adapter, command_dir):
        command_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in command_dir
            )
        return [htypes.view.command_source_d(command_dir_refs), *adapter.dir_list[-1]]

    async def save_history_and_open_piece(self, piece, command_dir):
        adapter = await self._adapter_factory(piece)
        origin_dir = self._origin_dir(adapter, command_dir)
        self._history.append(self._current_history_item)
        await self._open_object(piece, adapter, origin_dir)

    @property
    def _current_history_item(self):
        return _HistoryItem(self._current_piece, self._current_origin_dir, self._current_view.state)

    async def _open_object(self, piece, adapter, origin_dir, view_state=None):
        view = await self._create_view(adapter, origin_dir, view_state)
        self._current_adapter = adapter
        self._current_piece = piece
        self._current_origin_dir = origin_dir
        owner = self._current_view.parent().parent()  # Assuming parent is tab view; todo: unhack.
        self._current_view = view
        owner.replace_qt_widget(self)
        await self._command_hub.update()

    async def _create_view(self, adapter, origin_dir, view_state=None):
        view = await self._view_producer.create_view(adapter, add_dir_list=[origin_dir])
        if view_state is not None:
            view.state = view_state
        return view

    @command
    async def go_backward(self):
        try:
            item = self._history.move_backward(self._current_history_item)
        except IndexError:
            return
        adapter = await self._adapter_factory(item.piece)
        await self._open_object(item.piece, adapter, item.origin_dir, item.view_state)

    @command
    async def go_forward(self):
        try:
            item = self._history.move_forward(self._current_history_item)
        except IndexError:
            return
        adapter = await self._adapter_factory(item.piece)
        await self._open_object(item.piece, adapter, item.origin_dir, item.view_state)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_registry.register_actor(
            htypes.navigator.navigator,
            Navigator.from_state,
            services.mosaic,
            services.async_web,
            services.adapter_factory,
            services.object_commands_factory,
            services.view_producer,
            services.global_command_list,
            )
