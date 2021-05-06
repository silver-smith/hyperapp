from hyperapp.common.htypes import record_service_t
from hyperapp.common.module import Module

from .record_service import RecordService


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

    async def async_init(self, services):
        services.object_registry.register_actor(
            record_service_t, RecordService.from_piece,
            services.client_identity, services.mosaic, services.object_animator, services.command_registry,
            services.client_rpc_endpoint, services.async_rpc_proxy)
