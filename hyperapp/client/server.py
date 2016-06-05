import logging
import asyncio
import uuid
from PySide import QtCore
from ..common.util import is_list_inst
from ..common.endpoint import Endpoint, Url
from ..common.visual_rep import pprint
from ..common.htypes import tClientPacket, Interface, iface_registry
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
        log.info('send_notification command_id=%r notification=%r', notification.command_id, notification)
        self._send(notification.to_data())

    @asyncio.coroutine
    def execute_request( self, request ):
        assert isinstance(request, Request), repr(request)
        request_id = str(uuid.uuid4())
        log.info('execute_request command_id=%r request_id=%r', request.command_id, request_id)
        app = QtCore.QCoreApplication.instance()
        app.response_mgr.register_request(request_id, request)
        self._send(request.to_data(request_id))

    def _send( self, request_rec ):
        log.info('packet to %s', self.endpoint)
        pprint(tClientPacket, request_rec)
        transport_registry.send_packet(self, request_rec, tClientPacket)
