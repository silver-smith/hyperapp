from collections import namedtuple
from functools import partial

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

from . import htypes


RpcRequest = namedtuple('RpcRequest', 'receiver_identity sender')


class RpcEndpoint:

    def __init__(self, web, mosaic, types, peer_registry, transport):
        self._mosaic = mosaic
        self._types = types
        self._peer_registry = peer_registry
        self._transport = transport
        self._servant_by_id = {}
        self._message_registry = registry = CodeRegistry('rpc_message', web, types)
        registry.register_actor(htypes.rpc.request, self._handle_request)

    def register_servant(self, object_id, servant):
        self._servant_by_id[object_id] = servant

    def process(self, request):
        self._message_registry.invite(request.ref_list[0], request)

    def _handle_request(self, request, transport_request):
        receiver_identity = transport_request.receiver_identity
        sender = self._peer_registry.invite(request.sender_peer_ref)
        iface = self._types.resolve(request.iface_ref)
        iface_method = iface.methods[request.method_name]
        servant = self._servant_by_id[request.object_id]
        params = self._types.resolve_ref(request.params_ref).value
        method = getattr(servant, request.method_name)
        result = method(
            RpcRequest(transport_request.receiver_identity, sender),
            **params._asdict(),
            )
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


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.rpc_endpoint = partial(
            RpcEndpoint, services.web, services.mosaic, services.types, services.peer_registry, services.transport)
