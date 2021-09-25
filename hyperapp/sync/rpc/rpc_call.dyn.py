import logging
import uuid
from functools import partial

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.rpc_call = partial(self.rpc_call_factory, services.mosaic, services.transport)

    @staticmethod
    def rpc_call_factory(mosaic, transport, rpc_endpoint, receiver_peer, servant_path, sender_identity, timeout_sec=10):
        sender_peer_ref = mosaic.put(sender_identity.peer.piece)

        def call(*args):
            params = [
                mosaic.put(arg)
                for arg in args
                ]
            request_id = str(uuid.uuid4())
            request = htypes.rpc.request(
                request_id=request_id,
                servant_path=servant_path.as_data,
                params=params,
                sender_peer_ref=sender_peer_ref,
                )
            request_ref = mosaic.put(request)
            log.info("Rpc call: send rpc request: %s", request)
            transport.send(receiver_peer, sender_identity, [request_ref])
            result = rpc_endpoint.wait_for_response(request_id, timeout_sec)
            log.info("Rpc call: got result: %s", result)
            return result

        return call
