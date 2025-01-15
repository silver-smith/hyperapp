import logging
import inspect
import threading
import traceback
from collections import namedtuple
from functools import partial

from hyperapp.boot.htypes import HException

from . import htypes
from .services import (
    code_registry_ctr,
    deduce_t,
    mosaic,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


RpcRequest = namedtuple('RpcRequest', 'system receiver_identity sender')


class RpcEndpoint:

    def __init__(self, rpc_message_creg):
        self._rpc_message_creg = rpc_message_creg

    def __repr__(self):
        return '<sync RpcEndpoint>'

    def process(self, request):
        log.debug("Received rpc message: %s", request)
        self._rpc_message_creg.invite(request.ref_list[0], request)


def rpc_message_creg(config):
    return code_registry_ctr('rpc_message_creg', config)


def rpc_endpoint(rpc_message_creg):
    return RpcEndpoint(rpc_message_creg)


def rpc_request_futures():
    request_id_to_future = {}
    yield request_id_to_future
    log.info("Rpc endpoint: Shutting down: Cancelling futures: %s", request_id_to_future)
    for future in request_id_to_future.values():
        future.cancel()


def cancel_rpc_request_futures(rpc_request_futures):
    def _cancel_rpc_request_futures():
        log.info("Rpc endpoint: Cancelling futures: %s", rpc_request_futures)
        for future in rpc_request_futures.values():
            future.cancel()
        rpc_request_futures.clear()
    return _cancel_rpc_request_futures


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


def rpc_target_creg(config):
    return code_registry_ctr('rpc_target_creg', config)


def on_rpc_request(request, transport_request, system, transport, peer_registry, rpc_target_creg):
    log.info("Process rpc request: %s", request)
    receiver_identity = transport_request.receiver_identity
    sender = transport_request.sender
    rpc_request = RpcRequest(system, receiver_identity, sender)
    try:
        result = rpc_target_creg.invite(request.target, rpc_request)
        if type(result) is list:
            result = tuple(result)
        result_t = deduce_t(result)
        result_ref = mosaic.put(result, result_t)
        response = htypes.rpc.response(
            request_id=request.request_id,
            result_ref=result_ref,
            )
    except HException as x:
        log.info("Rpc target %s call h-typed error: %s", request.target, x)
        response = htypes.rpc.error_response(
            request_id=request.request_id,
            exception_ref=mosaic.put(x),
            )
    except Exception as x:
        traceback_entries = []
        cause = x
        while cause:
            traceback_entries += traceback.format_tb(cause.__traceback__)
            cause = cause.__cause__
        exception = htypes.rpc.server_error(str(x), tuple(traceback_entries))
        log.info(
            "Rpc target %s server error: %s\n%s",
            request.target, exception.message, "".join(exception.traceback))
        response = htypes.rpc.error_response(
            request_id=request.request_id,
            exception_ref=mosaic.put(exception),
            )
    response_ref = mosaic.put(response)
    transport.send(sender, receiver_identity, [response_ref])


def _params_to_kw(params):
    return {
        p.name: mosaic.resolve_ref(p.value).value
        for p in params
        }

        
def run_function_target(target, rpc_request):
    log.debug("Resolve rpc servant: %s", target.servant_ref)
    servant_fn = pyobj_creg.invite(target.servant_ref)
    kw = _params_to_kw(target.params)
    if 'request' in inspect.signature(servant_fn).parameters:
        kw = {**kw, 'request': rpc_request}
    log.info("Call rpc servant: %s (%s)", servant_fn, kw)
    result = servant_fn(**kw)
    log.info("Rpc servant %s call result: %s", servant_fn, result)
    return result


def run_service_target(target, rpc_request, system):
    log.debug("Resolve rpc service: %r", target.service_name)
    service = system.resolve_service(target.service_name)
    kw = _params_to_kw(target.params)
    log.info("Call rpc service: %s (%s)", service, kw)
    result = service(**kw)
    log.info("Rpc service %s call result: %s", service, result)
    return result
