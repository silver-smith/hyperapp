from hyperapp.common.htypes import service_t
from hyperapp.common.module import Module

from .list_service import ListService


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

    async def async_init(self, services):
        services.object_registry.register_actor(
            service_t, ListService.from_piece,
            services.client_identity, services.mosaic, services.types, services.command_registry,
            services.client_rpc_endpoint, services.async_rpc_proxy)
