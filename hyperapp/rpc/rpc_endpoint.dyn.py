import logging
import inspect
import threading
import traceback
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes import HException

from . import htypes
from .services import (
    code_registry_ctr,
    deduce_t,
    mark,
    mosaic,
    on_stop,
    peer_registry,
    pyobj_creg,
    transport,
    )

log = logging.getLogger(__name__)


RpcRequest = namedtuple('RpcRequest', 'receiver_identity sender')


class RpcEndpoint:

    def __init__(self):
        self._future_by_request_id = {}
        self._response_lock = threading.Lock()
        self._message_registry = registry = code_registry_ctr('rpc_message')
        self._is_stopping = False
        registry.register_actor(htypes.rpc.request, self._handle_request)
        registry.register_actor(htypes.rpc.response, self._handle_response)
        registry.register_actor(htypes.rpc.error_response, self._handle_error_response)

    def __repr__(self):
        return '<sync RpcEndpoint>'

    def stop(self):
        log.info("Stop rpc endpoint")
        with self._response_lock:
            self._is_stopping = True
            for future in self._future_by_request_id.values():
                future.cancel()

    def assign_future_to_request_id(self, request_id, future):
        with self._response_lock:
            self._future_by_request_id[request_id] = future

    def process(self, request):
        log.debug("Received rpc message: %s", request)
        self._message_registry.invite(request.ref_list[0], request)

    def _handle_request(self, request, transport_request):
        log.info("Process rpc request: %s", request)
        receiver_identity = transport_request.receiver_identity
        sender = peer_registry.invite(request.sender_peer_ref)
        servant_fn = "<unknown servant>"
        try:
            log.debug("Resolve rpc servant: %s", request.servant_ref)
            servant_fn = pyobj_creg.invite(request.servant_ref)
            params = {
                p.name: mosaic.resolve_ref(p.value).value
                for p in request.params
                }
            rpc_request = RpcRequest(receiver_identity, sender)
            kw = params
            if 'request' in inspect.signature(servant_fn).parameters:
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

    def _handle_response(self, response, transport_request):
        log.debug("Process rpc response: %s", response)
        result = mosaic.resolve_ref(response.result_ref).value
        with self._response_lock:
            future = self._future_by_request_id.pop(response.request_id)
            future.set_result(result)

    def _handle_error_response(self, response, transport_request):
        exception = mosaic.resolve_ref(response.exception_ref).value
        log.info("Process rpc error response: %s", exception)
        with self._response_lock:
            future = self._future_by_request_id.pop(response.request_id)
            future.set_exception(exception)


@mark.service
def rpc_endpoint_factory():
    def _rpc_endpoint_factory():
        endpoint = RpcEndpoint()
        _endpoint_list.append(endpoint)
        return endpoint
    return _rpc_endpoint_factory


def stop():
    for endpoint in _endpoint_list:
        endpoint.stop()


_endpoint_list = []
on_stop.append(stop)
