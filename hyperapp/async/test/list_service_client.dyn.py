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

        self._types = services.types
        self._async_rpc_endpoint = services.async_rpc_endpoint

        list_service_bundle = packet_coders.decode('cdr', config['list_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(list_service_bundle)
        list_service_ref = list_service_bundle.roots[0]
        self._list_service = services.mosaic.resolve_ref(list_service_ref).value
        self._list_service_type = services.types.resolve(self._list_service.type_ref)

        self._my_identity = services.generate_rsa_identity(fast=True)

    async def async_init(self, services):
        log.info("List service service async run:")
        try:
            rpc_endpoint = self._async_rpc_endpoint()
            services.async_endpoint_registry.register(self._my_identity, rpc_endpoint)
            iface_ref = self._types.reverse_resolve(self._list_service_type.interface)
            service = htypes.rpc.endpoint(
                peer_ref=self._list_service.peer_ref,
                iface_ref=iface_ref,
                object_id=self._list_service.object_id,
                )
            self._master_proxy = services.async_rpc_proxy(self._my_identity, rpc_endpoint, service)

            rows = await self._master_proxy.get()
            log.info("Returned rows: %s", rows)
        except Exception as x:
            log.exception("List service async run is failed:")
        log.info("List service async run: done.")
