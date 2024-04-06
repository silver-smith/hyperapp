import logging
import uuid
from concurrent.futures import Future
from functools import partial

from hyperapp.common.htypes import HException
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    mark,
    mosaic,
    transport,
    types,
    )

log = logging.getLogger(__name__)


def _rpc_submit_factory(rpc_endpoint, receiver_peer, servant_ref, sender_identity):
    sender_peer_ref = mosaic.put(sender_identity.peer.piece)

    def submit(**kw):
        params = tuple(
            htypes.rpc.param(
                name=name,
                value=mosaic.put(value, deduce_complex_value_type(mosaic, types, value)),
                )
            for name, value in kw.items()
            )
        request_id = str(uuid.uuid4())
        request = htypes.rpc.request(
            request_id=request_id,
            servant_ref=servant_ref,
            params=params,
            sender_peer_ref=sender_peer_ref,
            )
        request_ref = mosaic.put(request)
        future = Future()
        rpc_endpoint.assign_future_to_request_id(request_id, future)
        log.info("Rpc call: %s %s (%s): send rpc request: %s", receiver_peer, servant_ref, kw, request)
        transport.send(receiver_peer, sender_identity, [request_ref])
        return future

    return submit


@mark.service
def rpc_submit_factory():
    return _rpc_submit_factory


@mark.service
def rpc_call_factory():

    def factory(rpc_endpoint, receiver_peer, servant_ref, sender_identity, timeout_sec=10):
        submit_factory = _rpc_submit_factory(rpc_endpoint, receiver_peer, servant_ref, sender_identity)

        def call(**kw):
            future = submit_factory(**kw)
            try:
                result = future.result(timeout_sec)
            except HException as x:
                if isinstance(x, htypes.rpc.server_error):
                    log.error("Rpc call: got server error: %s\n%s", x.message, "".join(x.traceback))
                raise
            log.info("Rpc call: got result: %s", result)
            return result

        return call

    return factory
