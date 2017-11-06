import asyncio
import uuid
from ..common.htypes import IfaceCommand
from ..common.url import Url, UrlWithRoutes
from .request import ClientNotification, Request
from .server import Server
from .module import Module


class ProxyMethod(object):

    def __init__(self, packet_types, iface, server, path, command):
        self._packet_types = packet_types
        self._iface = iface
        self._server = server
        self._path = path
        self._command = command

    @asyncio.coroutine
    def __call__(self, *args, **kw):
        params = self._iface.make_params(self._command.command_id, *args, **kw)
        if self._command.request_type == IfaceCommand.rt_request:
            request_id = str(uuid.uuid4())
            request = Request(self._packet_types, self._iface, self._path, self._command.command_id, request_id, params)
            response = yield from self._server.execute_request(request)
            if response.error is not None:
                raise response.error
            else:
                return response.result
        elif self._command.request_type == IfaceCommand.rt_notification:
            notification = ClientNotification(self._packet_types, self._iface, self._path, self._command.command_id, params)
            yield from self._server.send_notification(notification)
        else:
            assert False, repr(self._command.request_type)

        
class RemotingProxy(object):

    def __init__(self, packet_types, iface, server, path):
        self._packet_types = packet_types
        self._iface = iface
        self._server = server
        self._path = path

    def get_url(self):
        return self._server.make_url(self._iface, self._path)

    def __getattr__(self, name):
        command = self._iface.get_command_if_exists(name)
        if not command:
            raise AttributeError(name)
        return ProxyMethod(self._packet_types, self._iface, self._server, self._path, command)


class ProxyFactory(object):

    def __init__(self, packet_types, remoting):
        self._packet_types = packet_types
        self._remoting = remoting

    def from_url(self, url):
        assert isinstance(url, Url), repr(url)
        if isinstance(url, UrlWithRoutes):
            self._remoting.add_routes(url.public_key, url.routes)
        server = Server.from_public_key(self._remoting, url.public_key)
        return RemotingProxy(self._packet_types, url.iface, server, url.path)
        
        
class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.proxy_factory = ProxyFactory(services.types.packet, services.remoting)
