import uuid

from hyperapp.common.module import Module

from . import htypes


class Method:

    def __init__(self, ref_registry, my_identity, my_peer_ref, peer, iface_ref, object_id, method_name, command):
        self._ref_registry = ref_registry
        self._my_identity = my_identity
        self._my_peer_ref = my_peer_ref
        self._method_name = method_name
        self._peer = peer
        self._iface_ref = iface_ref
        self._object_id = object_id
        self._method_name = method_name
        self._command = command

    def __call__(self, *args, **kw):
        # params = self._command.params_t(*args, **kw)
        # params_ref = self._ref_registry.distil(params)
        # request_id = str(uuid.uuid4())
        # request = htypes.rpc.request(
        #     sender_peer_ref=self._my_peer_ref,
        #     iface_ref=self._iface_ref,
        #     object_id=self._object_id,
        #     request_id=request_id,
        #     method_name=self._method_name,
        #     params_ref=params_ref,
        #     )
        raise NotImplementedError('todo')


class Proxy:

    def __init__(self, ref_registry, my_identity, my_peer_ref, peer, iface, iface_ref, object_id):
        self._ref_registry = ref_registry
        self._my_identity = my_identity
        self._my_peer_ref = my_peer_ref
        self._peer = peer
        self._iface_ref = iface_ref
        self._object_id = object_id
        for name, command in iface.items():
            method = Method(
                self._ref_registry, self._my_identity, self._my_peer_ref, self._peer, self._iface_ref, self._object_id, name, command)
            setattr(self, name, method)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._ref_registry = services.ref_registry
        self._types = services.types
        self._peer_registry = services.peer_registry
        services.rpc_proxy = self.rpc_proxy_factory

    def rpc_proxy_factory(self, my_identity, rpc_service):
        my_peer_ref = self._ref_registry.distil(my_identity.peer.piece)
        peer = self._peer_registry.invite(rpc_service.peer_ref)
        iface = self._types.resolve(rpc_service.iface_ref)
        return Proxy(self._ref_registry, my_identity, my_peer_ref, peer, iface, rpc_service.iface_ref, rpc_service.object_id)
