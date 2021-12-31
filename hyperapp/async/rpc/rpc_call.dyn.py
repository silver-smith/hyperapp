import logging
import uuid
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.async_rpc_call_factory = partial(self.rpc_call_factory, services.mosaic, services.types, services.async_transport)

    @staticmethod
    def rpc_call_factory(mosaic, types, async_transport, async_rpc_endpoint, receiver_peer, servant_ref, sender_identity):
        sender_peer_ref = mosaic.put(sender_identity.peer.piece)

        async def call(*args):
            params = [
                mosaic.put(arg, deduce_complex_value_type(mosaic, types, arg))
                for arg in args
                ]
            request_id = str(uuid.uuid4())
            request = htypes.rpc.request(
                request_id=request_id,
                servant_ref=servant_ref,
                params=params,
                sender_peer_ref=sender_peer_ref,
                )
            request_ref = mosaic.put(request)
            log.info("Rpc call: send rpc request: %s", request)
            await async_transport.send(receiver_peer, sender_identity, [request_ref])
            result = await async_rpc_endpoint.wait_for_response(request_id)
            log.info("Rpc call: got result: %s", result)
            return result

        return call
