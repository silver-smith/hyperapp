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
        super().__init__(module_name)

        master_service_bundle = packet_coders.decode('cdr', config['master_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(master_service_bundle)
        master_service_ref = master_service_bundle.roots[0]
        master_service = services.types.resolve_ref(master_service_ref).value

        my_identity = services.generate_rsa_identity(fast=True)
        my_peer_ref = services.mosaic.put(my_identity.peer.piece)

        echo_iface_ref = services.types.reverse_resolve(htypes.echo.echo_iface)

        rpc_endpoint = services.async_rpc_endpoint()
        services.async_endpoint_registry.register(my_identity, rpc_endpoint)

        echo_object_id = 'echo'

        servant = Echo()
        rpc_endpoint.register_servant(echo_object_id, servant)

        echo_service = htypes.rpc.endpoint(
            peer_ref=my_peer_ref,
            iface_ref=echo_iface_ref,
            object_id=echo_object_id,
            )
        self._echo_service_ref = services.mosaic.put(echo_service)

        self._master_proxy = services.async_rpc_proxy(my_identity, rpc_endpoint, master_service)

    async def async_init(self, services):
        log.info("Echo service async run:")
        try:
            await self._master_proxy.run(self._echo_service_ref)
        except Exception as x:
            log.exception("Echo service async run is failed:")
        log.info("Echo service async run: done.")
