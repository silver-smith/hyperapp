import logging
import inspect
import threading
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes import HException
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type
from hyperapp.common.code_registry import CodeRegistry

from . import htypes
from .services import (
    mark,
    mosaic,
    on_stop,
    peer_registry,
    python_object_creg,
    transport,
    types,
    web,
    )

log = logging.getLogger(__name__)


class TimeoutWaitingForResponse(Exception):
    pass


RpcRequest = namedtuple('RpcRequest', 'receiver_identity sender')


class SuccessResponse:

    def __init__(self, result):
        self._result = result

    def get_result(self):
        return self._result


class ErrorResponse:

    def __init__(self, exception):
        self._exception = exception

    def get_result(self):
        raise self._exception


class RpcEndpoint:

    def __init__(self):
        self._result_by_request_id = {}
        self._response_lock = threading.Lock()
        self._response_available = threading.Condition(self._response_lock)
        self._message_registry = registry = CodeRegistry('rpc_message', web, types)
        self._is_stopping = False
        registry.register_actor(htypes.rpc.request, self._handle_request)
        registry.register_actor(htypes.rpc.response, self._handle_response)
        registry.register_actor(htypes.rpc.error_response, self._handle_error_response)
        _endpoint_list.append(self)

    def __repr__(self):
        return '<sync RpcEndpoint>'

    def stop(self):
        log.info("Stop rpc endpoint")
        with self._response_lock:
            self._is_stopping = True
            self._response_available.notify_all()

    def wait_for_response(self, request_id, timeout_sec=10):
        log.debug("Wait for rpc response (timeout %s): %s", timeout_sec, request_id)
        with self._response_lock:
            while True:
                if self._is_stopping:
                    log.warning("Services are stopping, but we are still waiting for response for request: %s", request_id)
                    raise RuntimeError("Services are stopping")
                try:
                    response = self._result_by_request_id.pop(request_id)
                    return response.get_result()
                except KeyError:
                    if not self._response_available.wait(timeout_sec):
                        raise TimeoutWaitingForResponse(f"Timed out waiting for response (timeout {timeout_sec} seconds)")

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
            servant_fn = python_object_creg.invite(request.servant_ref)
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
            result_t = deduce_complex_value_type(mosaic, types, result)
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
            exception = htypes.rpc.server_error(str(x))
            log.exception("Rpc servant %s call error: %s", servant_fn, exception)
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
            self._result_by_request_id[response.request_id] = SuccessResponse(result)
            self._response_available.notify_all()

    def _handle_error_response(self, response, transport_request):
        exception = mosaic.resolve_ref(response.exception_ref).value
        log.info("Process rpc error response: %s", exception)
        with self._response_lock:
            self._result_by_request_id[response.request_id] = ErrorResponse(exception)
            self._response_available.notify_all()


@mark.service
def rpc_endpoint_factory():
    return RpcEndpoint


def stop():
    for endpoint in _endpoint_list:
        endpoint.stop()


_endpoint_list = []
on_stop.append(stop)
