import logging
import inspect
import threading
import traceback
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes import HException

from . import htypes
from .services import (
    code_registry_ctr2,
    deduce_t,
    mosaic,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


RpcRequest = namedtuple('RpcRequest', 'receiver_identity sender')


class RpcEndpoint:

    def __init__(self, rpc_message_creg):
        self._rpc_message_creg = rpc_message_creg

    def __repr__(self):
        return '<sync RpcEndpoint>'

    def process(self, request):
        log.debug("Received rpc message: %s", request)
        self._rpc_message_creg.invite(request.ref_list[0], request)


def rpc_message_creg(config):
    return code_registry_ctr2('rpc-message', config)


def rpc_endpoint(rpc_message_creg):
    return RpcEndpoint(rpc_message_creg)


def rpc_request_futures():
    request_id_to_future = {}
    yield request_id_to_future
    for future in request_id_to_future.values():
        future.cancel()


def on_rpc_request(request, transport_request, transport, peer_registry):
    log.info("Process rpc request: %s", request)
    receiver_identity = transport_request.receiver_identity
    sender = transport_request.sender
    servant_fn = "<unknown servant>"
    try:
        log.debug("Resolve rpc servant: %s", request.servant_ref)
        servant_fn = pyobj_creg.invite(request.servant_ref)
        kw = {
            p.name: mosaic.resolve_ref(p.value).value
            for p in request.params
            }
        if 'request' in inspect.signature(servant_fn).parameters:
            rpc_request = RpcRequest(receiver_identity, sender)
            kw = {**kw, 'request': rpc_request}
        log.info("Call rpc servant: %s (%s)", servant_fn, kw)
        result = servant_fn(**kw)
        log.info("Rpc servant %s call result: %s", servant_fn, result)
        if type(result) is list:
            result = tuple(result)
        result_t = deduce_t(result)
        result_ref = mosaic.put(result, result_t)
        response = htypes.rpc.response(
            request_id=request.request_id,
            result_ref=result_ref,
            )
    except HException as x:
        log.info("Rpc servant %s call h-typed error: %s", servant_fn, x)
        response = htypes.rpc.error_response(
            request_id=request.request_id,
            exception_ref=mosaic.put(x),
            )
    except Exception as x:
        traceback_entries = tuple(traceback.format_tb(x.__traceback__))
        exception = htypes.rpc.server_error(str(x), traceback_entries)
        log.info(
            "Rpc servant %s server error: %s\n%s",
            servant_fn, exception.message, "".join(exception.traceback))
        response = htypes.rpc.error_response(
            request_id=request.request_id,
            exception_ref=mosaic.put(exception),
            )
    response_ref = mosaic.put(response)
    transport.send(sender, receiver_identity, [response_ref])


def on_rpc_response(response, transport_request, rpc_request_futures):
    log.debug("Process rpc response: %s", response)
    result = mosaic.resolve_ref(response.result_ref).value
    future = rpc_request_futures.pop(response.request_id)
    future.set_result(result)


def on_rpc_error_response(response, transport_request, rpc_request_futures):
    exception = mosaic.resolve_ref(response.exception_ref).value
    log.info("Process rpc error response: %s", exception)
    future = rpc_request_futures.pop(response.request_id)
    future.set_exception(exception)
