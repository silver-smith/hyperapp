import logging
import uuid
from functools import partial

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class Proxy:

    def __init__(self, mosaic, transport, my_identity, my_peer_ref, rpc_endpoint, peer, iface, iface_ref, object_id):
        self._mosaic = mosaic
        self._transport = transport
        self._my_identity = my_identity
        self._my_peer_ref = my_peer_ref
        self._rpc_endpoint = rpc_endpoint
        self._peer = peer
        self._iface_ref = iface_ref
        self._object_id = object_id
        for name, method in iface.methods.items():
            method = partial(self._run_request, name, method)
            setattr(self, name, method)

    def _run_request(self, method_name, method, *args, **kw):
        params = method.params_record_t(*args, **kw)
        log.info("Rpc proxy call: %s(%s)", method_name, params)
        params_ref = self._mosaic.put(params)
        request_id = str(uuid.uuid4())
        request = htypes.rpc.request(
            sender_peer_ref=self._my_peer_ref,
            iface_ref=self._iface_ref,
            object_id=self._object_id,
            request_id=request_id,
            method_name=method_name,
            params_ref=params_ref,
            )
        request_ref = self._mosaic.put(request)
        log.info("Send rpc request: %s", request)
        self._transport.send(self._peer, self._my_identity, [request_ref])
        result = self._rpc_endpoint.wait_for_response(request_id)
        log.info("Rpc proxy: got result: %s", result)
        return result


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._mosaic = services.mosaic
        self._types = services.types
        self._peer_registry = services.peer_registry
        self._transport = services.transport
        services.rpc_proxy = self.rpc_proxy_factory

    def rpc_proxy_factory(self, my_identity, rpc_endpoint, rpc_service):
        my_peer_ref = self._mosaic.put(my_identity.peer.piece)
        peer = self._peer_registry.invite(rpc_service.peer_ref)
        iface = self._types.resolve(rpc_service.iface_ref)
        return Proxy(self._mosaic, self._transport, my_identity, my_peer_ref, rpc_endpoint, peer, iface, rpc_service.iface_ref, rpc_service.object_id)
