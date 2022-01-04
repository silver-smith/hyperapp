from hyperapp.common.module import Module

from . import htypes
from .live_list_service import LiveListService


class ThisModule(Module):

    async def async_init(self, services):
        services.object_registry.register_actor(
            htypes.service.live_list_service,
            LiveListService.from_piece,
            services.mosaic,
            services.types,
            services.async_web,
            services.command_registry,
            services.peer_registry,
            services.client_identity,
            services.client_rpc_endpoint,
            services.async_rpc_call_factory,
            )
        services.python_object_creg.register_actor(
            htypes.service.live_list_service,
            LiveListService.from_piece,
            services.mosaic,
            services.types,
            services.async_web,
            services.command_registry,
            services.peer_registry,
            services.client_identity,
            services.client_rpc_endpoint,
            services.async_rpc_call_factory,
            )
