from PySide import QtCore, QtNetwork
from ..common.identity import PublicKey
from ..common.tcp_packet import has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet
from ..common.transport_packet import decode_transport_packet
from .util import call_in_future
from .transport import transport_registry
from .transport_session import TransportSessionList


RECONNECT_INTERVAL_MS = 2000


class TcpConnection(object):

    _connections = {}  # (server public key, host, port) -> Connection

    @classmethod
    def produce( cls, server_public_key, host, port ):
        key = (server_public_key.get_id(), host, port)
        connection = cls._connections.get(key)
        if not connection:
            connection = cls(server_public_key, host, port)
            cls._connections[key] = connection
        return connection

    def __init__( self, server_public_key, host, port ):
        assert isinstance(server_public_key, PublicKey), repr(server_public_key)
        self.server_public_key = server_public_key
        self.host = host
        self.port = port
        self.session_list = TransportSessionList()
        self.socket = None
        self.connected = False
        self.send_buf = ''
        self.recv_buf = ''
        self.trace('connecting...')
        self.socket = QtNetwork.QTcpSocket()
        self.socket.error.connect(self.on_error)
        self.socket.stateChanged.connect(self.on_state_changed)
        self.socket.hostFound.connect(self.on_host_found)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.bytesWritten.connect(self.on_bytes_written)
        self.socket.readyRead.connect(self.on_ready_read)
        self._connect()

    def get_session_list( self ):
        return self.session_list

    def _connect( self ):
        self.socket.connectToHost(self.host, self.port)

    def trace( self, msg ):
        print 'tcp to %s at %s:%d: %s' % (self.server_public_key.get_short_id_hex(), self.host, self.port, msg)

    def on_error( self, error ):
        self.trace('Error: %s' % error)
        if error == QtNetwork.QAbstractSocket.ConnectionRefusedError:
            call_in_future(RECONNECT_INTERVAL_MS, self._connect)

    def on_state_changed( self, state ):
        self.trace('State changed: %r' % state)

    def on_host_found( self ):
        self.trace('Host found')

    def on_connected( self ):
        self.trace('Connected, %d bytes in send buf' % len(self.send_buf))
        self.connected = True
        if self.send_buf:
            self.socket.write(self.send_buf)

    def on_disconnected( self ):
        self.trace('Disconnected')
        self.connected = False
        self.recv_buf = ''
        self._connect()

    def on_bytes_written( self, size ):
        self.send_buf = self.send_buf[size:]
        self.trace('%d bytes is written, %d bytes to go' % (size, len(self.send_buf)))
        if self.send_buf:
            self.socket.write(self.send_buf)

    def on_ready_read( self ):
        data = str(self.socket.readAll())
        self.trace('%d bytes is received' % len(data))
        self.recv_buf += data
        while self.recv_buf:
            if not has_full_tcp_packet(self.recv_buf): break
            packet_data, packet_size = decode_tcp_packet(self.recv_buf)
            transport_packet = decode_transport_packet(packet_data)
            transport_registry.process_packet(self, self.session_list, self.server_public_key, transport_packet)
            assert packet_size <= len(self.recv_buf), repr(packet_size)
            self.recv_buf = self.recv_buf[packet_size:]
            self.trace('consumed %d bytes, remained %d' % (packet_size, len(self.recv_buf)))

    def send_data( self, contents ):
        assert isinstance(contents, str), repr(contents)
        data = encode_tcp_packet(contents)
        self.trace('sending data, old=%d, write=%d, new=%d' % (len(self.send_buf), len(data), len(self.send_buf) + len(data)))
        if self.connected and not self.send_buf:
            self.socket.write(data)
        self.send_buf += data  # may be sent partially, will send remainder on bytesWritten signal

    def __del__( self ):
        print '~TcpConnection', self.host, self.port
