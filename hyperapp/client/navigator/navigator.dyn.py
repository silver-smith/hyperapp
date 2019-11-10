# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from functools import partial

from hyperapp.client.commander import FreeFnCommand
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .view_registry import Item, VisualTree, ViewHandler

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

    def __init__(self, module, command_registry, view_opener, object):
        self._module = module
        self._command_registry = command_registry
        self._view_opener = view_opener
        self._object = object

    def current_changed(self, current_item_key):
        self._module._update_element_commands(self._command_registry, self._view_opener, self._object, current_item_key)


class NavigatorHandler(ViewHandler):

    def __init__(self, state, object_registry, view_producer_registry, module_command_registry, async_ref_resolver):
        super().__init__()
        self._state = state
        self._object_registry = object_registry
        self._view_producer_registry = view_producer_registry
        self._module_command_registry = module_command_registry
        self._async_ref_resolver = async_ref_resolver
        self._history = _History()

    async def create_view(self, command_registry, view_opener=None):
        piece = await self._async_ref_resolver.resolve_ref_to_object(self._state.current_piece_ref)
        object = self._object_registry.resolve(piece)
        command_registry.set_commands('layout', list(self._get_layout_commands(command_registry, view_opener)))
        command_registry.set_commands('global', list(self._get_global_commands(command_registry, view_opener)))
        command_registry.set_commands('object', list(self._get_object_commands(command_registry, view_opener, object)))
        self._history.append(piece)
        return (await self._view_producer_registry.produce_view(piece, object))

    async def visual_tree(self):
        piece = await self._async_ref_resolver.resolve_ref_to_object(self._state.current_piece_ref)
        return VisualTree('Navigator', {(): [Item(0, 'current', str(piece))]})

    def _get_global_commands(self, command_registry, view_opener):
        for command in self._module_command_registry.get_all_commands():
            yield FreeFnCommand.from_command(command, partial(self._run_command, command_registry, view_opener, command))

    def _get_object_commands(self, command_registry, view_opener, object):
        for command in object.get_command_list():
            if command.kind != 'object':
                continue
            yield FreeFnCommand.from_command(command, partial(self._run_command, command_registry, view_opener, command))

    def _get_element_commands(self, command_registry, view_opener, object, current_item_key):
        for command in object.get_item_command_list(current_item_key):
            yield FreeFnCommand.from_command(command, partial(self._run_command, command_registry, view_opener, command, current_item_key))

    def _get_layout_commands(self, command_registry, view_opener):
        yield self._go_backward.partial(command_registry, view_opener)
        yield self._go_forward.partial(command_registry, view_opener)

    async def _run_command(self, command_registry, view_opener, command, *args, **kw):
        piece = await command.run(*args, **kw)
        if piece is None:
            return
        await self._open_piece(piece, command_registry, view_opener)
        self._history.append(piece)

    async def _open_piece(self, piece, command_registry, view_opener):
        object = await self._object_registry.resolve_async(piece)
        self._current_item_observer = observer = _CurrentItemObserver(self, command_registry, view_opener, object)
        view = await self._view_producer_registry.produce_view(piece, object, observer)
        view_opener.open(view)
        command_registry.set_commands('object', list(self._get_object_commands(command_registry, view_opener, object)))
        command_registry.set_commands('element', [])

    def _update_element_commands(self, command_registry, view_opener, object, current_item_key):
        command_registry.set_commands('element', list(self._get_element_commands(command_registry, view_opener, object, current_item_key)))

    @command('go_backward')
    async def _go_backward(self, command_registry, view_opener):
        try:
            piece = self._history.move_backward()
        except IndexError:
            return
        await self._open_piece(piece, command_registry, view_opener)

    @command('go_forward')
    async def _go_forward(self, command_registry, view_opener):
        try:
            piece = self._history.move_forward()
        except IndexError:
            return
        await self._open_piece(piece, command_registry, view_opener)


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
