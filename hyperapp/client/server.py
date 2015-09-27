from PySide import QtNetwork
from ..common.packet import Packet
from ..common.packet_coders import packet_coders
from ..common.visual_rep import pprint
from ..common.interface import Interface, iface_registry
from ..common.packet_container import tPacketContainer
from ..common.request import (
    tServerPacket,
    tClientPacket,
    ClientNotification,
    Request,
    ServerNotification,
    Response,
    decode_server_packet,
    )
from .module_loader import load_client_module
from .proxy_registry import proxy_registry


PACKET_ENCODING = 'cdr'


class Connection(object):

    addr2connection = {}

    @classmethod
    def get_connection( cls, addr ):
        connection = cls.addr2connection.get(addr)
        if not connection:
            connection = Connection(addr)
            cls.addr2connection[addr] = connection
        return connection

    def __init__( self, addr ):
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
                       % (packet.encoding, len(self.recv_buf), len(packet.contents)))
            Server(self.addr).process_packet(packet)

    def send_packet( self, packet ):
        data = packet.encode()
        self.trace('sending data, old=%d, write=%d, new=%d' % (len(self.send_buf), len(data), len(self.send_buf) + len(data)))
        if self.connected and not self.send_buf:
            self.socket.write(data)
        self.send_buf += data  # may be sent partially, will send remainder on bytesWritten signal

    def __del__( self ):
        print '~Connection', self.addr


class Server(object):

    @classmethod
    def resolve_locator( cls, locator ):
        host, port_str = locator.split(':')
        addr = (host, int(port_str))
        return cls(addr)

    def __init__( self, addr ):
        self.addr = addr

    def get_locator( self ):
        host, port = self.addr
        return '%s:%r' % (host, port)

    def resolve_object( self, objinfo ):
        proxy_obj = proxy_registry.resolve(self, objinfo.path, objinfo.proxy_id, objinfo.iface)
        proxy_obj.set_contents(objinfo.contents)
        return proxy_obj

    def send_notification( self, notification ):
        assert isinstance(notification, ClientNotification), repr(notification)
        print 'send_notification', notification.command_id, notification
        self._send(notification)

    def execute_request( self, request, resp_handler ):
        assert isinstance(request, Request), repr(request)
        request_id = request.request_id
        print 'execute_request', request.command_id, request_id
        proxy_registry.register_resp_handler(request_id, resp_handler)
        self._send(request)

    def _send( self, request ):
        encoding = PACKET_ENCODING
        print '%s packet to %s:%d' % (encoding, self.addr[0], self.addr[1])
        pprint(tClientPacket, request)
        packet = packet_coders.encode_packet(encoding, request, tClientPacket)
        Connection.get_connection(self.addr).send_packet(packet)

    def process_packet( self, packet ):
        print 'processing %s packet: %d bytes' % (packet.encoding, len(packet.contents))
        container = packet_coders.decode_packet(packet, tPacketContainer, iface_registry)
        self._process_aux_packet(container)
        response = decode_server_packet(self, iface_registry, packet.encoding, container.packet)
        print '%s packet from %s:%d' % (packet.encoding, self.addr[0], self.addr[1])
        ## pprint(tServerPacket, response)
        if isinstance(response, Response):
            print '   response for request', response.command_id, response.request_id
            proxy_registry.process_received_response(self, response)
        else:
            assert isinstance(response, ServerNotification), repr(response)
            proxy_registry.process_received_notification(self, response)

    def _process_aux_packet( self, container ):
        #pprint(tPacketContainer, container)
        for module in container.modules:
            print '-- loading module %r fpath=%r' % (module.id, module.fpath)
            load_client_module(module)
