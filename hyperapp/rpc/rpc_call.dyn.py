import logging
import uuid
from concurrent.futures import Future
from functools import partial

from hyperapp.common.htypes import HException

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    )

log = logging.getLogger(__name__)


def _param_value_to_ref(value):
    t = deduce_t(value)
    if type(value) is list:
        value = tuple(value)
    return mosaic.put(value, t)


def rpc_submit_target_factory(transport, rpc_request_futures, receiver_peer, servant_ref, sender_identity):

    def submit(target):
        request_id = str(uuid.uuid4())
        request = htypes.rpc.request(
            request_id=request_id,
            target=mosaic.put(target),
            )
        request_ref = mosaic.put(request)
        future = Future()
        rpc_request_futures[request_id] = future
        log.info("Rpc call target: receiver=%s: send rpc request %s: %s", receiver_peer, request_ref, request)
        transport.send(receiver_peer, sender_identity, [request_ref])
        return future

    return submit


def rpc_submit_factory(rpc_submit_target_factory, receiver_peer, servant_ref, sender_identity):
    submit_factory = rpc_submit_target_factory(receiver_peer, servant_ref, sender_identity)

    def submit(**kw):
        params = tuple(
            htypes.rpc.param(
                name=name,
                value=_param_value_to_ref(value),
                )
            for name, value in kw.items()
            )
        target = htypes.rpc.function_target(
            servant_ref=servant_ref,
            params=params,
            )
        log.info("Rpc call: receiver=%s servant=%s (%s): send rpc request: %s", receiver_peer, servant_ref, kw, target)
        return submit_factory(target)

    return submit


def rpc_call_factory(rpc_submit_factory, receiver_peer, servant_ref, sender_identity, timeout_sec=10):
    submit_factory = rpc_submit_factory(receiver_peer, servant_ref, sender_identity)

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
