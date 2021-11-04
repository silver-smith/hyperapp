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

    async def raise_unexpected_error(self, request):
        log.info("Echo.make_unexpected_error: request=%s", request)
        raise RuntimeError("Some unexpected error")

    async def raise_test_error(self, request):
        log.info("Echo.raise_test_error: request=%s", request)
        raise htypes.echo_service.test_error("Some error")


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._async_rpc_endpoint_factory = services.async_rpc_endpoint_factory
        self._async_endpoint_registry = services.async_endpoint_registry

        master_service_bundle = packet_coders.decode('cdr', config['master_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(master_service_bundle)
        master_peer_ref, *master_servant_path_refs = master_service_bundle.roots

        self._master_peer = services.peer_registry.invite(master_peer_ref)
        self._master_servant_path = services.servant_path_from_data(master_servant_path_refs)

        self._my_identity = services.generate_rsa_identity(fast=True)
        self._my_peer_ref = services.mosaic.put(self._my_identity.peer.piece)

    async def async_init(self, services):
        log.info("Echo service async run:")
        try:
            echo_servant_name = 'echo'
            echo_servant_path = services.servant_path().registry_name(echo_servant_name)

            rpc_endpoint = self._async_rpc_endpoint_factory()
            self._async_endpoint_registry.register(self._my_identity, rpc_endpoint)
            rpc_call = services.async_rpc_call(rpc_endpoint, self._master_peer, self._master_servant_path, self._my_identity)

            servant = Echo()
            rpc_endpoint.register_servant(echo_servant_name, servant)

            await rpc_call(self._my_peer_ref, echo_servant_path.as_data)
        except Exception as x:
            log.exception("Echo service async run is failed:")
        log.info("Echo service async run: done.")
