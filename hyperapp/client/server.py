from PySide import QtCore, QtNetwork
from ..common.util import path2str, str2path
from ..common.packet import Packet
from ..common.visual_rep import pprint
from ..common.interface import Interface, iface_registry
from ..common.request import (
    tServerPacket,
    tClientPacket,
    ClientNotification,
    Request,
    Response,
    decode_server_packet,
    )
from .objimpl_registry import objimpl_registry
from .proxy_registry import proxy_registry


PACKET_ENCODING = 'cdr'


class RespHandler(object):

    def __init__( self, iface, command_id ):
        assert isinstance(iface, Interface), repr(iface)
        assert isinstance(command_id, basestring), repr(command_id)
        self.iface = iface
        self.command_id = command_id

    def process_response( self, server, response ):
        raise NotImplementedError(self.__class__)


class Connection(object):

    def __init__( self, server, addr ):
        self.server = server
        self.addr = addr
        self.socket = None
        self.connected = False
        self.send_buf = ''
        self.recv_buf = ''
        host, port = self.addr
        print 'Network: connecting to %s:%d' % (host, port)
        self.socket = QtNetwork.QTcpSocket()
        self.socket.error.connect(self.on_error)
        self.socket.stateChanged.connect(self.on_state_changed)
        self.socket.hostFound.connect(self.on_host_found)
        self.socket.connected.connect(self.on_connected)
        self.socket.bytesWritten.connect(self.on_bytes_written)
        self.socket.readyRead.connect(self.on_ready_read)
        self.socket.connectToHost(host, port)

    def trace( self, msg ):
        host, port = self.addr
        print 'Network, connection to %s:%d %s' % (host, port, msg)

    def on_error( self, msg ):
        self.trace('Error: %s' % msg)

    def on_state_changed( self, state ):
        self.trace('State changed: %r' % state)

    def on_host_found( self ):
        self.trace('Host found')

    def on_connected( self ):
        self.trace('Connected, %d bytes in send buf' % len(self.send_buf))
        self.connected = True
        if self.send_buf:
            self.socket.write(self.send_buf)

    def on_bytes_written( self, size ):
        self.send_buf = self.send_buf[size:]
        self.trace('%d bytes is written, %d bytes to go' % (size, len(self.send_buf)))
        if self.send_buf:
            self.socket.write(self.send_buf)

    def on_ready_read( self ):
        data = str(self.socket.readAll())
        self.trace('%d bytes is received' % len(data))
        self.recv_buf += data
        while Packet.is_full(self.recv_buf):
            packet, self.recv_buf = Packet.decode(self.recv_buf)
            self.trace('received %s packet (%d bytes remainder): size=%d'
                       % (packet.encoding, len(self.recv_buf), len(packet.data)))
            self.server.process_packet(packet)

    def send_packet( self, packet ):
        data = packet.encode()
        self.trace('sending data, old=%d, write=%d, new=%d' % (len(self.send_buf), len(data), len(self.send_buf) + len(data)))
        if self.connected and not self.send_buf:
            self.socket.write(data)
        self.send_buf += data  # may be sent partially, will send remainder on bytesWritten signal

    def __del__( self ):
        print '~Connection', self.addr


class Server(object):

    addr2server = {}  # (host, port) -> Server

    @classmethod
    def resolve_locator( cls, locator ):
        host, port_str = locator.split(':', 1)
        addr = (host, int(port_str))
        return cls.resolve_addr(addr)

    @classmethod
    def resolve_addr( cls, addr ):
        server = cls.addr2server.get(addr)
        if not server:
            server = cls(addr)
            cls.addr2server[addr] = server
        return server

    @classmethod
    def decode_url( cls, url ):
        locator, path_str = url.split('/', 1)
        server = cls.resolve_locator(locator)
        path = str2path(path_str)
        return (server, path)

    def __init__( self, addr ):
        self.addr = addr
        self._connection = None
        self.pending_requests = {}  # request_id -> RespHandler

    def encode_url( self, iface, path ):
        return '%s/%s' % (self.get_locator(), path2str(path))

    def get_locator( self ):
        host, port = self.addr
        return '%s:%r' % (host, port)

    def __repr__( self ):
        return self.get_locator()

    def _get_connection( self ):
        if not self._connection:
            self._connection = Connection(self, self.addr)
        return self._connection

    def resolve_object( self, objinfo ):
        return objimpl_registry.produce_obj(self, objinfo)

    def send_notification( self, notification ):
        assert isinstance(notification, ClientNotification), repr(notification)
        print 'send_notification', notification.command_id, notification
        self._send(notification)

    def execute_request( self, request, resp_handler ):
        assert isinstance(request, Request), repr(request)
        assert isinstance(resp_handler, RespHandler), repr(resp_handler)
        request_id = request.request_id
        assert request_id not in self.pending_requests, repr(request_id)
        print 'execute_request', request.command_id, request_id
        self.pending_requests[request_id] = resp_handler
        self._send(request)

    def _send( self, request ):
        encoding = PACKET_ENCODING
        print '%s packet to %s:%d' % (encoding, self.addr[0], self.addr[1])
        pprint(tClientPacket, request)
        packet = Packet.from_contents(encoding, request, tClientPacket)
        self._get_connection().send_packet(packet)

    def process_packet( self, packet ):
        print '%r from %s:%d' % (packet, self.addr[0], self.addr[1])
        app = QtCore.QCoreApplication.instance()
        app.add_modules(packet.aux.modules)
        if app.has_unfulfilled_requirements(packet.aux.requirements):
            app.request_required_modules_and_reprocess_packet(self, packet)
        else:
            self._process_packet(packet)

    def reprocess_packet( self, packet ):
        print 'reprocessing %r from %s:%d' % (packet, self.addr[0], self.addr[1])
        app = QtCore.QCoreApplication.instance()
        app.add_modules(packet.aux.modules)
        assert not app.has_unfulfilled_requirements(packet.aux.requirements)  # still has unfilfilled requirements
        self._process_packet(packet)

    def _process_packet( self, packet ):
        response_or_notification = packet.decode_server_packet(self, iface_registry)
        self._process_updates(response_or_notification.updates)
        if isinstance(response_or_notification, Response):
            response = response_or_notification
            print '   response for request', response.command_id, response.request_id
            resp_handler = self.pending_requests.get(response.request_id)
            if not resp_handler:
                print 'Received response #%s for a missing (already destroyed) object, ignoring' % response.request_id
                return
            del self.pending_requests[response.request_id]
            resp_handler.process_response(self, response)

    def _process_updates( self, updates ):
        for update in updates:
            obj = proxy_registry.resolve(server, update.path)
            if obj:
                obj.process_update(update.diff)
            # otherwize object is already gone and updates must be discarded
