import logging
import threading

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

        self._async_rpc_endpoint = services.async_rpc_endpoint

        master_service_bundle = packet_coders.decode('cdr', config['master_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(master_service_bundle)
        master_service_ref = master_service_bundle.roots[0]
        self._master_service = services.mosaic.resolve_ref(master_service_ref).value

        self._my_identity = services.generate_rsa_identity(fast=True)

    async def async_init(self, services):
        log.info("List service service async run:")
        try:
            rpc_endpoint = self._async_rpc_endpoint()
            services.async_endpoint_registry.register(self._my_identity, rpc_endpoint)
            self._master_proxy = services.async_rpc_proxy(self._my_identity, rpc_endpoint, self._master_service)

            rows = await self._master_proxy.get()
            log.info("Returned rows: %s", rows)
        except Exception as x:
            log.exception("List service async run is failed:")
        log.info("List service async run: done.")
