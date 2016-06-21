import logging
import asyncio
from ..common.identity import PublicKey
from ..common.endpoint import Endpoint, Url
from ..common.route_storage import RouteStorage
from ..common.visual_rep import pprint
from .request import ClientNotification, Request
from .transport import transport_registry

log = logging.getLogger(__name__)


class Server(object):

    _servers = {}  # public key -> Server

    @classmethod
    def from_endpoint( cls, endpoint ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        RouteStorage.instance.add_routes(endpoint.public_key, endpoint.routes)
        server = cls._servers.get(endpoint.public_key)
        if not server:
            server = Server(endpoint.public_key)
            cls._servers[endpoint.public_key] = server
        return server

    @classmethod
    def from_public_key( cls, public_key ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        server = cls._servers.get(public_key)
        if not server:
            server = Server(public_key)
            cls._servers[public_key] = server
        return server

    def __init__( self, public_key ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        self.public_key = public_key
        self._route_storage = RouteStorage.instance

    def get_endpoint( self ):
        routes = self._route_storage.get_routes(self.public_key)
        return Endpoint(self.public_key, routes)

    def get_id( self ):
        return self.public_key.get_id()

    def make_url( self, iface, path ):
        return Url(iface, path, self.get_endpoint())

    def __repr__( self ):
        return 'server:%s' % self.public_key.get_short_id_hex()

    def send_notification( self, notification ):
        assert isinstance(notification, ClientNotification), repr(notification)
        log.info('notification command_id=%r to %s', notification.command_id, self.public_key.get_short_id_hex())
        return (yield from transport_registry.send_notification(self.get_endpoint(), notification))

    @asyncio.coroutine
    def execute_request( self, request ):
        assert isinstance(request, Request), repr(request)
        log.info('request command_id=%r request_id=%r to %s', request.command_id, request.request_id, self.public_key.get_short_id_hex())
        return (yield from transport_registry.execute_request(self.get_endpoint(), request))
