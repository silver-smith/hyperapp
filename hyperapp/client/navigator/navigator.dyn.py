# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from functools import partial

from hyperapp.client.commander import FreeFnCommand
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .view_handler import RootVisualItem, VisualItem, ViewHandler

_log = logging.getLogger(__name__)


class _History:

    def __init__(self):
        self._backward_piece_list = []  # last element is current piece
        self._forward_piece_list = []

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


class _CurrentItemObserver:

    def __init__(self, handler, object):
        self._handler = handler
        self._object = object

    def current_changed(self, current_item_key):
        self._handler._update_element_commands(self._object, current_item_key)


class NavigatorHandler(ViewHandler):

    def __init__(self, state, path, command_registry, view_opener, object_registry, view_producer_registry, module_command_registry, async_ref_resolver):
        super().__init__()
        self._state = state
        self._command_registry = command_registry
        self._view_opener = view_opener
        self._object_registry = object_registry
        self._view_producer_registry = view_producer_registry
        self._module_command_registry = module_command_registry
        self._async_ref_resolver = async_ref_resolver
        self._history = _History()

    async def create_view(self):
        piece = await self._async_ref_resolver.resolve_ref_to_object(self._state.current_piece_ref)
        object = self._object_registry.resolve(piece)
        self._command_registry.set_commands('view', list(self._get_view_commands()))
        self._command_registry.set_commands('global', list(self._get_global_commands()))
        self._command_registry.set_commands('object', list(self._get_object_commands(object)))
        self._history.append(piece)
        return (await self._view_producer_registry.produce_view(piece, object))

    async def visual_item(self):
        piece = await self._async_ref_resolver.resolve_ref_to_object(self._state.current_piece_ref)
        return RootVisualItem('Navigator', children=[
            VisualItem(0, 'current', str(piece)),
            ])

    def _get_global_commands(self):
        for command in self._module_command_registry.get_all_commands():
            yield FreeFnCommand.from_command(command, partial(self._run_command, command))

    def _get_object_commands(self, object):
        for command in object.get_command_list():
            if command.kind != 'object':
                continue
            yield FreeFnCommand.from_command(command, partial(self._run_command, command))

    def _get_element_commands(self, object, current_item_key):
        for command in object.get_item_command_list(current_item_key):
            yield FreeFnCommand.from_command(command, partial(self._run_command, command, current_item_key))

    def _get_view_commands(self):
        yield self._go_backward
        yield self._go_forward

    async def _run_command(self, command, *args, **kw):
        piece = await command.run(*args, **kw)
        if piece is None:
            return
        await self._open_piece(piece)
        self._history.append(piece)

    async def _open_piece(self, piece):
        object = await self._object_registry.resolve_async(piece)
        self._current_item_observer = observer = _CurrentItemObserver(self, object)
        view = await self._view_producer_registry.produce_view(piece, object, observer)
        self._view_opener.open(view)
        self._command_registry.set_commands('object', list(self._get_object_commands(object)))
        self._command_registry.set_commands('element', [])

    def _update_element_commands(self, object, current_item_key):
        self._command_registry.set_commands('element', list(self._get_element_commands(object, current_item_key)))

    @command('go_backward')
    async def _go_backward(self):
        try:
            piece = self._history.move_backward()
        except IndexError:
            return
        await self._open_piece(piece)

    @command('go_forward')
    async def _go_forward(self):
        try:
            piece = self._history.move_forward()
        except IndexError:
            return
        await self._open_piece(piece)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_registry.register_type(
            htypes.navigator.navigator,
            NavigatorHandler,
            services.object_registry,
            services.view_producer_registry,
            services.module_command_registry,
            services.async_ref_resolver,
            )
