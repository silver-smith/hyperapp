import logging

from hyperapp.common.htypes import bundle_t, list_service_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from .list_service import ListService

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

        self._object_registry = services.object_registry
        self._async_rpc_endpoint = services.async_rpc_endpoint

        list_service_bundle = packet_coders.decode('cdr', config['list_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(list_service_bundle)
        self._list_service_ref = list_service_bundle.roots[0]

        self._my_identity = services.generate_rsa_identity(fast=True)

    async def async_init(self, services):
        log.info("List service async run:")

        rpc_endpoint = services.async_rpc_endpoint()
        services.async_endpoint_registry.register(self._my_identity, rpc_endpoint)

        services.object_registry.register_actor(
            list_service_t, ListService.from_piece,
            self._my_identity, services.mosaic, services.types, rpc_endpoint, services.async_rpc_proxy)

        try:
            object = await self._object_registry.invite(self._list_service_ref)

            rows = await object.get_all_items()
            log.info("Returned rows: %s", rows)
        except Exception as x:
            log.exception("List service async run is failed:")
        log.info("List service async run: done.")
