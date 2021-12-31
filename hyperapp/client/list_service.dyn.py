from hyperapp.common.module import Module

from . import htypes
from .list_service import ListService


class ThisModule(Module):

    async def async_init(self, services):
        services.object_registry.register_actor(
            htypes.service.list_service,
            ListService.from_piece,
            services.mosaic,
            services.types,
            services.async_web,
            services.command_registry,
            services.peer_registry,
            services.client_identity,
            services.client_rpc_endpoint,
            services.async_rpc_call_factory,
            )
