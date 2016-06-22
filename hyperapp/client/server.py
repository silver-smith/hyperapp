import logging
import asyncio
from ..common.identity import PublicKey
from ..common.endpoint import Endpoint, Url
from ..common.visual_rep import pprint
from .request import ClientNotification, Request
from .transport import TransportRegistry

log = logging.getLogger(__name__)


class Server(object):

    _servers = {}  # public key -> Server

    @classmethod
    def from_public_key( cls, transport_registry, public_key ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        server = cls._servers.get(public_key)
        if not server:
            server = Server(transport_registry, public_key)
            cls._servers[public_key] = server
        return server

    def __init__( self, transport_registry, public_key ):
        assert isinstance(transport_registry, TransportRegistry), repr(transport_registry)
        assert isinstance(public_key, PublicKey), repr(public_key)
        self._transport_registry = transport_registry
        self.public_key = public_key

    def get_id( self ):
        return self.public_key.get_id()

    def make_url( self, iface, path ):
        return Url(iface, path, Endpoint(self.public_key, []))

    def __repr__( self ):
        return 'server:%s' % self.public_key.get_short_id_hex()

    def send_notification( self, notification ):
        assert isinstance(notification, ClientNotification), repr(notification)
        log.info('notification command_id=%r to %s', notification.command_id, self.public_key.get_short_id_hex())
        return (yield from self._transport_registry.send_notification(self.public_key, notification))

    @asyncio.coroutine
    def execute_request( self, request ):
        assert isinstance(request, Request), repr(request)
        log.info('request command_id=%r request_id=%r to %s', request.command_id, request.request_id, self.public_key.get_short_id_hex())
        return (yield from self._transport_registry.execute_request(self.public_key, request))
