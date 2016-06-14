import logging
import asyncio
import uuid
from ..common.util import is_list_inst
from ..common.endpoint import Endpoint, Url
from ..common.visual_rep import pprint
from ..common.htypes import Interface, iface_registry
from .request import ClientNotification, Request
from .objimpl_registry import objimpl_registry
from .transport import transport_registry

log = logging.getLogger(__name__)


class Server(object):

    _servers = {}  # public key -> Server

    @classmethod
    def from_endpoint( cls, endpoint ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        server = cls._servers.get(endpoint.public_key)
        if not server:
            server = Server(endpoint)
            cls._servers[endpoint.public_key] = server
        return server

    def __init__( self, endpoint ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        self.endpoint = endpoint

    def get_endpoint( self ):
        return self.endpoint

    def get_id( self ):
        return self.endpoint.public_key.get_id()

    def make_url( self, iface, path ):
        return Url(iface, path, self.endpoint)

    def __repr__( self ):
        return 'server:%s' % self.endpoint

    def resolve_object( self, objinfo ):
        return objimpl_registry.produce_obj(self, objinfo)

    def send_notification( self, notification ):
        assert isinstance(notification, ClientNotification), repr(notification)
        log.info('notification command_id=%r to %s', notification.command_id, self.endpoint)
        return (yield from transport_registry.send_notification(self.get_endpoint(), notification))

    @asyncio.coroutine
    def execute_request( self, request ):
        assert isinstance(request, Request), repr(request)
        log.info('request command_id=%r request_id=%r to %s', request.command_id, request.request_id, self.endpoint)
        return (yield from transport_registry.execute_request(self.get_endpoint(), request))
