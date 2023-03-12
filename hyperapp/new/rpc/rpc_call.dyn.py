import logging
import uuid
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    mark,
    mosaic,
    transport,
    types,
    )

log = logging.getLogger(__name__)


@mark.service
def rpc_call_factory():

    def factory(rpc_endpoint, receiver_peer, servant_ref, sender_identity, timeout_sec=10):
        sender_peer_ref = mosaic.put(sender_identity.peer.piece)

        def call(**kw):
            params = [
                htypes.rpc.param(
                    name=name,
                    value=mosaic.put(value, deduce_complex_value_type(mosaic, types, value)),
                    )
                for name, value in kw.items()
                ]
            request_id = str(uuid.uuid4())
            request = htypes.rpc.request(
                request_id=request_id,
                servant_ref=servant_ref,
                params=params,
                sender_peer_ref=sender_peer_ref,
                )
            request_ref = mosaic.put(request)
            log.info("Rpc call: %s %s (%s): send rpc request: %s", receiver_peer, servant_ref, kw, request)
            transport.send(receiver_peer, sender_identity, [request_ref])
            result = rpc_endpoint.wait_for_response(request_id, timeout_sec)
            log.info("Rpc call: got result: %s", result)
            return result

        return call

    return factory
