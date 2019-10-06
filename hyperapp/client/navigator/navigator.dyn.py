# navigator component - container keeping navigation history and allowing go backward and forward

import logging

from hyperapp.client.module import ClientModule

from . import htypes
from .view import View

_log = logging.getLogger(__name__)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
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
        return (await view_producer_registry.produce_view(piece, object))
