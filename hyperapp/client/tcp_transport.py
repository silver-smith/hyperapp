from PySide import QtCore, QtNetwork
from ..common.packet import Packet
from .transport import Transport, transports


RECONNECT_INTERVAL_MS = 2000


class TcpConnection(Transport):

    def __init__( self, server, host, port ):
        self.server = server
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.send_buf = ''
        self.recv_buf = ''
        print 'Network: connecting to %s:%d' % (self.host, self.port)
        self.socket = QtNetwork.QTcpSocket()
        self.socket.error.connect(self.on_error)
        self.socket.stateChanged.connect(self.on_state_changed)
        self.socket.hostFound.connect(self.on_host_found)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.bytesWritten.connect(self.on_bytes_written)
        self.socket.readyRead.connect(self.on_ready_read)
        self._connect()

    def _connect( self ):
        self.socket.connectToHost(self.host, self.port)

    def trace( self, msg ):
        print 'Network, connection to %s:%d %s' % (self.host, self.port, msg)

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
        while Packet.has_full_packet(self.recv_buf):
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
        print '~Connection', self.host, self.port


class TcpTransport(Transport):

    connections = {}  # (server public key, host, port) -> Connection

    def send_packet( self, server, route, packet ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        connection = self.produce_connection(server, host, port)
        connection.send_packet(packet)

    def produce_connection( self, server, host, port ):
        key = (server.endpoint.public_key, host, port)
        connection = self.connections.get(key)
        if not connection:
            connection = TcpConnection(server, host, port)
            self.connections[key] = connection
        return connection


transports.register('tcp', TcpTransport())
