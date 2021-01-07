# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .layout import GlobalLayout
from .layout_command import LayoutCommand

_log = logging.getLogger(__name__)


_HistoryItem = namedtuple('_HistoryItem', 'object layout_handle')


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
            object_registry,
            object_layout_registry,
            layout_handle_from_object_type,
            module_command_registry,
            params_editor,
            ):
        self = cls(
            mosaic,
            async_web,
            object_registry,
            object_layout_registry,
            layout_handle_from_object_type,
            module_command_registry,
            params_editor,
            path,
            command_hub,
            view_opener,
            )
        await self._async_init(state.current_piece_ref)
        return self

    def __init__(
            self,
            mosaic,
            async_web,
            object_registry,
            object_layout_registry,
            layout_handle_from_object_type,
            module_command_registry,
            params_editor,
            path,
            command_hub,
            view_opener,
            ):
        super().__init__(path)
        self._mosaic = mosaic
        self._async_web = async_web
        self._object_registry = object_registry
        self._object_layout_registry = object_layout_registry
        self._layout_handle_from_object_type = layout_handle_from_object_type
        self._module_command_registry = module_command_registry
        self._params_editor = params_editor
        self._command_hub = command_hub
        self._view_opener = view_opener
        self._history = _History()
        self._current_object = None
        self._current_layout_handle = None
        self._current_view = None

    async def _async_init(self, initial_piece_ref):
        piece = await self._async_web.summon(initial_piece_ref)
        self._current_object = object = await self._object_registry.animate(piece)
        self._current_layout_handle = await self._layout_handle_from_object_type(object.type)
        self._history.append(_HistoryItem(object, None))

    @property
    def data(self):
        piece_ref = self._mosaic.put(self._current_object.data)
        return htypes.navigator.navigator(piece_ref)

    async def create_view(self):
        self._current_view = await self._current_layout_handle.layout.create_view(self._command_hub, self._current_object)
        return self._current_view

    async def visual_item(self):
        piece = self._current_object.data
        return self.make_visual_item('Navigator', children=[
            self.make_visual_item(str(piece), name='current'),
            ])

    def get_current_commands(self):
        return [
            *super().get_current_commands(),
            *self._get_global_commands(),
            *self._get_current_layout_commands(),
            ]

    def _get_global_commands(self):
        for command in self._module_command_registry.get_all_commands():
            yield (LayoutCommand(command.id, command)
                   .with_(wrapper=self._open_layout, layout_handle=self._current_layout_handle)
                   )

    def _get_current_layout_commands(self):
        current_layout_commands = self._current_layout_handle.layout.get_current_commands(
            self._current_object, self._current_view)
        for command in current_layout_commands:
            yield command.with_(wrapper=self._open_layout, layout_handle=self._current_layout_handle)

    async def _open_layout(self, resolved_piece):
        await self._open_layout_impl(resolved_piece.object, resolved_piece.layout_handle)
        self._history.append(_HistoryItem(resolved_piece.object, resolved_piece.layout_handle))

    async def _open_piece(self, piece):
        layout_handle = await self._open_piece_impl(piece)
        self._history.append(_HistoryItem(self._current_object, layout_handle))

    async def _open_piece_impl(self, piece):
        object = await self._object_registry.animate(piece)
        layout_handle = await self._open_object(object)
        return layout_handle

    async def _open_object(self, object):
        layout_handle = await self._layout_handle_from_object_type(object.type)
        await self._open_layout_impl(object, layout_handle)
        return layout_handle

    async def _open_layout_impl(self, object, layout_handle):
        view = await layout_handle.layout.create_view(self._command_hub, object)
        self._view_opener.open(view)
        self._current_object = object
        self._current_layout_handle = layout_handle
        self._current_view = view
        self._command_hub.update()

    @command('go_backward')
    async def _go_backward(self):
        try:
            item = self._history.move_backward()
        except IndexError:
            return
        await self._open_object(item.object)

    @command('go_forward')
    async def _go_forward(self):
        try:
            item = self._history.move_forward()
        except IndexError:
            return
        await self._open_object(item.object)

    @command('open_layout_editor')
    async def _open_layout_editor(self):
        object_type_ref = self._mosaic.put(self._current_object.type)
        piece = htypes.layout_editor.object_layout_editor(object_type_ref, origin_object_type_ref=None, origin_command_id=None)
        await self._open_piece(piece)

    @command('commands')
    async def _open_commands(self):
        piece_ref = self._mosaic.put(self._current_object.data)
        layout_handle_ref = self._mosaic.put(self._current_layout_handle.data)
        piece = htypes.command_list.command_list(piece_ref, layout_handle_ref)
        await self._open_piece(piece)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        services.view_registry.register_actor(
            htypes.navigator.navigator,
            NavigatorLayout.from_data,
            services.mosaic,
            services.async_web,
            services.object_registry,
            services.object_layout_registry,
            services.layout_handle_from_object_type,
            services.module_command_registry,
            services.params_editor,
            )
