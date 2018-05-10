from .module import ClientModule


MODULE_NAME = 'remoting_proxy'


class ProxyMethod(object):

    def __init__(self, remoting, transport_ref, iface, service_id, command):
        self._remoting = remoting
        self._transport_ref = transport_ref
        self._iface = iface
        self._service_id = service_id
        self._command = command

    async def __call__(self, *args, **kw):
        params = self._command.request(*args, **kw)
        return await self._remoting.send_request(self._transport_ref, self._iface, self._service_id, self._command, params)


class RemotingProxy(object):

    def __init__(self, remoting, transport_ref, iface, service_id):
        self._remoting = remoting
        self._transport_ref = transport_ref
        self._iface = iface
        self._service_id = service_id

    def __getattr__(self, name):
        command = self._iface.get(name)
        if not command:
            raise AttributeError(name)
        return ProxyMethod(self._remoting, self._transport_ref, self._iface, self._service_id, command)


class ProxyFactory(object):

    def __init__(self, types, remoting, async_ref_resolver):
        self._types = types
        self._remoting = remoting
        self._async_ref_resolver = async_ref_resolver

    async def from_ref(self, ref):
        service = await self._async_ref_resolver.resolve_ref_to_object(ref, expected_type='hyper_ref.service_ref')
        iface = self._types.resolve(service.iface_full_type_name)
        return RemotingProxy(self._remoting, service.transport_ref, iface, service.service_id)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.proxy_factory = ProxyFactory(services.types, services.remoting, services.async_ref_resolver)
