from hyperapp.common.module import Module

from . import htypes
from .record_service import RecordService


class ThisModule(Module):

    async def async_init(self, services):
        services.object_registry.register_actor(
            htypes.service.record_service,
            RecordService.from_piece,
            services.mosaic,
            services.async_web,
            services.object_factory,
            services.command_registry,
            services.peer_registry,
            services.client_identity,
            services.client_rpc_endpoint,
            services.async_rpc_call_factory,
            )
