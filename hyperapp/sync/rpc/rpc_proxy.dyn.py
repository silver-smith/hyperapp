from hyperapp.common.module import Module


class Method:

    def __init__(self, peer, iface, object_id):
        self._peer = peer
        self._iface = iface
        self._object_id = object_id

    def __call__(self, *args, **kw):
        raise NotImplementedError('todo')


class Proxy:

    def __init__(self, peer, iface, object_id):
        self._peer = peer
        self._iface = iface
        self._object_id = object_id
        for name, command in iface.items():
            setattr(self, name, Method(self._peer, self._iface, self._object_id))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._types = services.types
        self._peer_registry = services.peer_registry
        services.rpc_proxy = self.rpc_proxy_factory

    def rpc_proxy_factory(self, rpc_service):
        peer = self._peer_registry.invite(rpc_service.peer_ref)
        iface = self._types.resolve(rpc_service.iface_ref)
        return Proxy(peer, iface, rpc_service.object_id)
