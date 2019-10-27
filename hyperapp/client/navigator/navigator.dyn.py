# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from functools import partial

from hyperapp.client.commander import FreeFnCommand
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View

_log = logging.getLogger(__name__)


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
        command_registry.set_commands('global', list(self._get_global_commands(command_registry, view_opener)))
        command_registry.set_commands('object', list(self._get_object_commands(command_registry, view_opener, object)))
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

    async def _run_command(self, command_registry, view_opener, command, *args, **kw):
        piece = await command.run(*args, **kw)
        if piece is None:
            return
        object = await self._object_registry.resolve_async(piece)
        self._current_item_observer = observer = _CurrentItemObserver(self, command_registry, view_opener, object)
        view = await self._view_producer_registry.produce_view(piece, object, observer)
        view_opener.open(view)
        command_registry.set_commands('object', list(self._get_object_commands(command_registry, view_opener, object)))

    def _update_element_commands(self, command_registry, view_opener, object, current_item_key):
        command_registry.set_commands('element', list(self._get_element_commands(command_registry, view_opener, object, current_item_key)))
