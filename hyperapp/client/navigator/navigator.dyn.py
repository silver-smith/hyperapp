# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from functools import partial

from hyperapp.common.htypes import resource_key_t
from hyperapp.client.commander import FreeFnCommand
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View

_log = logging.getLogger(__name__)


class _History:

    def __init__(self):
        self._backward_piece_list = []
        self._forward_piece_list = []

    def append(self, piece):
        self._backward_piece_list.append(piece)
        self._forward_piece_list.clear()

    def move_backward(self):
        current_piece = self._backward_piece_list.pop()
        self._forward_piece_list.append(current_piece)
        return self._backward_piece_list[-1]

    def move_forward(self):
        current_piece = self._forward_piece_list.pop()
        self._backward_piece_list.append(current_piece)
        return current_piece


class _CurrentItemObserver:

    def __init__(self, module, command_registry, view_opener, object):
        self._module = module
        self._command_registry = command_registry
        self._view_opener = view_opener
        self._object = object

    def current_changed(self, current_item_key):
        self._module._update_element_commands(self._command_registry, self._view_opener, self._object, current_item_key)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._object_registry = services.object_registry
        self._view_producer_registry = services.view_producer_registry
        self._module_command_registry = services.module_command_registry
        self._history = _History()
        services.view_registry.register_type(
            htypes.navigator.navigator,
            self._resolve_data,
            services.async_ref_resolver,
            services.object_registry,
            services.view_producer_registry,
            )

    async def _resolve_data(self, state, command_registry, view_opener, async_ref_resolver, object_registry, view_producer_registry):
        piece = await async_ref_resolver.resolve_ref_to_object(state.current_piece_ref)
        object = object_registry.resolve(piece)
        command_registry.set_commands('layout', list(self._get_layout_commands(command_registry, view_opener)))
        command_registry.set_commands('global', list(self._get_global_commands(command_registry, view_opener)))
        command_registry.set_commands('object', list(self._get_object_commands(command_registry, view_opener, object)))
        self._history.append(piece)
        return (await view_producer_registry.produce_view(piece, object))

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
        yield FreeFnCommand('backward', 'layout', resource_key_t(__module_ref__, ['global', 'command', 'backward']), True,
                            partial(self._go_backward, command_registry, view_opener))
        yield FreeFnCommand('forward', 'layout', resource_key_t(__module_ref__, ['global', 'command', 'forward']), True,
                            partial(self._go_forward, command_registry, view_opener))

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

    def _update_element_commands(self, command_registry, view_opener, object, current_item_key):
        command_registry.set_commands('element', list(self._get_element_commands(command_registry, view_opener, object, current_item_key)))

    async def _go_backward(self, command_registry, view_opener):
        try:
            piece = self._history.move_backward()
        except IndexError:
            return
        await self._open_piece(piece, command_registry, view_opener)

    async def _go_forward(self, command_registry, view_opener):
        try:
            piece = self._history.move_forward()
        except IndexError:
            return
        await self._open_piece(piece, command_registry, view_opener)
