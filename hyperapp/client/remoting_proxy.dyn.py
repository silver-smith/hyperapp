import uuid

from ..common.interface import packet as packet_types
from ..common.htypes import IfaceCommand
from ..common.url import Url, UrlWithRoutes
from .request import ClientNotification, Request
from .server import Server
from .module import Module


class ProxyMethod(object):

    def __init__(self, iface, server, path, command):
        self._iface = iface
        self._server = server
        self._path = path
        self._command = command

    async def __call__(self, *args, **kw):
        params = self._iface.make_params(self._command.command_id, *args, **kw)
        if self._command.request_type == IfaceCommand.rt_request:
            request_id = str(uuid.uuid4())
            request = Request(packet_types, self._iface, self._path, self._command.command_id, request_id, params)
            response = await self._server.execute_request(request)
            if response.error is not None:
                raise response.error
            else:
                return response.result
        elif self._command.request_type == IfaceCommand.rt_notification:
            notification = ClientNotification(packet_types, self._iface, self._path, self._command.command_id, params)
            await self._server.send_notification(notification)
        else:
            assert False, repr(self._command.request_type)

        
class RemotingProxy(object):

    def __init__(self, iface, server, path):
        self._iface = iface
        self._server = server
        self._path = path

    def get_url(self):
        return self._server.make_url(self._iface, self._path)

    def __getattr__(self, name):
        command = self._iface.get_command_if_exists(name)
        if not command:
            raise AttributeError(name)
        return ProxyMethod(self._iface, self._server, self._path, command)


class ProxyFactory(object):

    def __init__(self, type_registry_registry, async_ref_resolver):
        self._type_registry_registry = type_registry_registry
        self._async_ref_resolver = async_ref_resolver

    async def from_ref(self, ref):
        service = await self._async_ref_resolver.resolve_ref_to_object(ref, expected_type='hyper_ref.service_ref')
        iface = self._type_registry_registry.resolve_type(service.iface_full_type_name)
        assert False, (service.iface_full_type_name, iface)

        assert isinstance(url, Url), repr(url)
        if isinstance(url, UrlWithRoutes):
            self._remoting.add_routes(url.public_key, url.routes)
        server = Server.from_public_key(self._remoting, url.public_key)
        return RemotingProxy(url.iface, server, url.path)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.proxy_factory = ProxyFactory(services.type_registry_registry, services.async_ref_resolver)
