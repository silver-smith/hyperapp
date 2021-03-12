import logging
import threading
from collections import namedtuple
from functools import partial

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


RpcRequest = namedtuple('RpcRequest', 'receiver_identity sender')


class RpcEndpoint:

    def __init__(self, web, mosaic, types, peer_registry, transport):
        self._mosaic = mosaic
        self._types = types
        self._peer_registry = peer_registry
        self._transport = transport
        self._servant_by_id = {}
        self._result_by_request_id = {}
        self._response_lock = threading.Lock()
        self._response_available = threading.Condition(self._response_lock)
        self._message_registry = registry = CodeRegistry('rpc_message', web, types)
        registry.register_actor(htypes.rpc.request, self._handle_request)
        registry.register_actor(htypes.rpc.response, self._handle_response)

    def register_servant(self, object_id, servant):
        self._servant_by_id[object_id] = servant

    def wait_for_response(self, request_id, timeout_sec=10):
        log.info("Wait for rpc response (timeout %s): %s", timeout_sec, request_id)
        with self._response_lock:
            while True:
                try:
                    return self._result_by_request_id.pop(request_id)
                except KeyError:
                    if not self._response_available.wait(timeout_sec):
                        raise RuntimeError(f"Timed out waiting for response (timeout {timeout_sec} seconds)")

    def process(self, request):
        log.info("Received rpc message: %s", request)
        self._message_registry.invite(request.ref_list[0], request)

    def _handle_request(self, request, transport_request):
        log.info("Process rpc request: %s", request)
        receiver_identity = transport_request.receiver_identity
        sender = self._peer_registry.invite(request.sender_peer_ref)
        iface = self._types.resolve(request.iface_ref)
        iface_method = iface.methods[request.method_name]
        servant = self._servant_by_id[request.object_id]
        params = self._mosaic.resolve_ref(request.params_ref).value
        log.info("Call rpc servant: %s(%s)", request.method_name, params)
        method = getattr(servant, request.method_name)
        result = method(
            RpcRequest(transport_request.receiver_identity, sender),
            **params._asdict(),
            )
        log.info("Rpc servant call result: %s", result)
        response_record_t = iface_method.response_record_t
        if not isinstance(result, tuple):
            if not response_record_t.fields:
                if result is not None:
                    raise RuntimeError(f"{iface.name}.{request.method_name} expected no response, but returned: {result!r}")
                result = ()
            elif len(response_record_t.fields) == 1:
                result = (result,)  # Accept simple result.
        result_record = response_record_t(*result)
        result_ref = self._mosaic.put(result_record)
        response = htypes.rpc.response(
            request_id=request.request_id,
            result_ref=result_ref,
            )
        response_ref = self._mosaic.put(response)
        self._transport.send(sender, receiver_identity, [response_ref])

    def _handle_response(self, response, transport_request):
        log.info("Process rpc response: %s", response)
        result = self._mosaic.resolve_ref(response.result_ref).value
        with self._response_lock:
            self._result_by_request_id[response.request_id] = result
            self._response_available.notify_all()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.rpc_endpoint = partial(
            RpcEndpoint, services.web, services.mosaic, services.types, services.peer_registry, services.transport)
