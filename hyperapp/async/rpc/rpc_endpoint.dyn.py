import asyncio
import logging
import time
from collections import namedtuple
from functools import partial

from hyperapp.common.module import Module

from . import htypes
from .code_registry import CodeRegistry

log = logging.getLogger(__name__)


RpcRequest = namedtuple('RpcRequest', 'receiver_identity sender')


class RpcEndpoint:

    def __init__(self, async_web, mosaic, types, peer_registry, transport):
        self._mosaic = mosaic
        self._types = types
        self._peer_registry = peer_registry
        self._transport = transport
        self._servant_by_id = {}
        self._result_by_request_id = {}
        self._response_available = asyncio.Condition()
        self._message_registry = registry = CodeRegistry('rpc_message', async_web, types)
        registry.register_actor(htypes.rpc.request, self._handle_request)
        registry.register_actor(htypes.rpc.response, self._handle_response)

    def register_servant(self, object_id, servant):
        self._servant_by_id[object_id] = servant

    async def wait_for_response(self, request_id, timeout_sec=20):
        log.info("Wait for rpc response (timeout %s): %s", timeout_sec, request_id)
        timeout_at = time.monotonic() + timeout_sec
        remaining = timeout_at - time.monotonic()
        async with self._response_available:
            while remaining > 0:
                try:
                    return self._result_by_request_id.pop(request_id)
                except KeyError:
                    pass
                try:
                    await asyncio.wait_for(self._response_available.wait(), remaining)
                except asyncio.TimeoutError:
                    break
                remaining = timeout_at - time.monotonic()
        raise RuntimeError(f"Timed out waiting for response (timeout {timeout_sec} seconds)")

    async def process(self, request):
        log.info("Received rpc message: %s", request)
        await self._message_registry.invite(request.ref_list[0], request)

    async def _handle_request(self, request, transport_request):
        log.info("Process rpc request: %s", request)
        receiver_identity = transport_request.receiver_identity
        sender = self._peer_registry.invite(request.sender_peer_ref)
        iface = self._types.resolve(request.iface_ref)
        iface_method = iface.methods[request.method_name]
        servant = self._servant_by_id[request.object_id]
        params = self._types.resolve_ref(request.params_ref).value
        log.info("Call rpc servant: %s(%s)", request.method_name, params)
        method = getattr(servant, request.method_name)
        rpc_request = RpcRequest(transport_request.receiver_identity, sender)
        result = await method(rpc_request, **params._asdict())
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
        await self._transport.send(sender, receiver_identity, [response_ref])

    async def _handle_response(self, response, transport_request):
        log.info("Process rpc response: %s", response)
        result = self._types.resolve_ref(response.result_ref).value
        async with self._response_available:
            self._result_by_request_id[response.request_id] = result
            self._response_available.notify_all()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.async_rpc_endpoint = partial(
            RpcEndpoint, services.async_web, services.mosaic, services.types, services.peer_registry, services.async_transport)
