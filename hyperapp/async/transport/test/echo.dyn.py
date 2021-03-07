import logging

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class Endpoint:

    def __init__(self, mosaic, transport, my_identity):
        self._mosaic = mosaic
        self._transport = transport
        self._my_identity = my_identity

    async def process(self, request):
        log.info("Echo endpoint: process request %s", request)
        my_peer_ref = self._mosaic.put(request.receiver_identity.peer.piece)
        self._transport.send(request.sender, self._my_identity, [*request.ref_list, my_peer_ref])


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

        master_peer_bundle = packet_coders.decode('cdr', config['master_peer_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(master_peer_bundle)
        master_peer_ref = master_peer_bundle.roots[0]

        self._master_peer = services.peer_registry.invite(master_peer_ref)
        self._my_identity = services.generate_rsa_identity(fast=True)
        self._my_peer_ref = services.mosaic.put(self._my_identity.peer.piece)

        endpoint = Endpoint(services.mosaic, services.transport, self._my_identity)
        services.async_endpoint_registry.register(self._my_identity, endpoint)

    async def async_init(self, services):
        log.info("Test async send:")
        await services.async_transport.send(self._master_peer, self._my_identity, [self._my_peer_ref])
        log.info("Test async send: done.")
