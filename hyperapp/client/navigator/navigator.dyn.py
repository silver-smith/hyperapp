# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from functools import partial

from hyperapp.client.module import ClientModule

from . import htypes
from .view import View

_log = logging.getLogger(__name__)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._module_command_registry = services.module_command_registry
        services.view_registry.register_type(
            htypes.navigator.navigator,
            self._resolve_data,
            services.async_ref_resolver,
            services.object_registry,
            services.view_producer_registry,
            )

    async def _resolve_data(self, state, command_registry, async_ref_resolver, object_registry, view_producer_registry):
        piece = await async_ref_resolver.resolve_ref_to_object(state.current_piece_ref)
        object = object_registry.resolve(piece)
        command_registry.set_commands('global', list(self._get_global_commands()))
        command_registry.set_commands('object', list(self._get_object_commands(object)))
        return (await view_producer_registry.produce_view(piece, object))

    def _get_global_commands(self):
        for command in self._module_command_registry.get_all_commands():
            yield partial(self._run_command, command)

    def _get_object_commands(self, object):
        for command in object.get_command_list():
            if command.kind != 'object':
                continue
            yield partial(self._run_command, command)

    async def _run_command(self, command):
        piece = await command.run()
        if piece is not None:
            await self._open(piece)

    async def _open(self, piece):
        assert 0  # todo
