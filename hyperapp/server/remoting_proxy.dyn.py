from hyperapp.common.module import Module
from . import htypes


MODULE_NAME = 'remoting_proxy'


class ProxyMethod(object):

    def __init__(self, remoting, service_ref, iface, command):
        self._remoting = remoting
        self._service_ref = service_ref
        self._iface = iface
        self._command = command

    def __call__(self, *args, **kw):
        params = self._command.request(*args, **kw)
        return self._remoting.send_request(self._service_ref, self._iface, self._command, params)


class RemotingProxy(object):

    def __init__(self, remoting, service_ref, iface):
        self._remoting = remoting
        self._service_ref = service_ref
        self._iface = iface

    @property
    def service_ref(self):
        return self._service_ref

    def __getattr__(self, name):
        command = self._iface.get(name)
        if not command:
            raise AttributeError(name)
        return ProxyMethod(self._remoting, self._service_ref, self._iface, command)


class ProxyFactory(object):

    def __init__(self, type_resolver, remoting):
        self._type_resolver = type_resolver
        self._remoting = remoting

    def from_ref(self, ref):
        service = self._type_resolver.resolve_ref_to_data(ref, expected_type=htypes.hyper_ref.service)
        iface = self._types.resolve(service.iface_full_type_name)
        return RemotingProxy(self._remoting, ref, iface)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.proxy_factory = ProxyFactory(services.type_resolver, services.remoting)
