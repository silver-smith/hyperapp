import logging
import threading

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class Echo:

    async def echo(self, request, message):
        log.info("Echo.echo: %s; request=%s", message, request)
        return f'{message} to you too'


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._async_rpc_endpoint = services.async_rpc_endpoint
        self._async_endpoint_registry = services.async_endpoint_registry

        master_service_bundle = packet_coders.decode('cdr', config['master_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(master_service_bundle)
        master_service_ref = master_service_bundle.roots[0]
        self._master_service = services.mosaic.resolve_ref(master_service_ref).value

        self._my_identity = services.generate_rsa_identity(fast=True)
        my_peer_ref = services.mosaic.put(self._my_identity.peer.piece)

        echo_iface_ref = services.types.reverse_resolve(htypes.echo.echo_iface)

        self._echo_object_id = 'echo'

        echo_service = htypes.rpc.endpoint(
            peer_ref=my_peer_ref,
            iface_ref=echo_iface_ref,
            object_id=self._echo_object_id,
            )
        self._echo_service_ref = services.mosaic.put(echo_service)

    async def async_init(self, services):
        log.info("Echo service async run:")
        try:
            rpc_endpoint = self._async_rpc_endpoint()
            self._async_endpoint_registry.register(self._my_identity, rpc_endpoint)
            master_proxy = services.async_rpc_proxy(self._my_identity, rpc_endpoint, self._master_service)

            servant = Echo()
            rpc_endpoint.register_servant(self._echo_object_id, servant)

            await master_proxy.run(self._echo_service_ref)
        except Exception as x:
            log.exception("Echo service async run is failed:")
        log.info("Echo service async run: done.")
