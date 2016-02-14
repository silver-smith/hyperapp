from PySide import QtCore, QtNetwork
from ..common.tcp_packet import encode_tcp_packet
from .util import call_in_future


RECONNECT_INTERVAL_MS = 2000


class TcpConnection(object):

    def __init__( self, host, port, data_consumer ):
        self.data_consumer = data_consumer
        self.host = host
        self.port = port
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

    def _connect( self ):
        self.socket.connectToHost(self.host, self.port)

    def trace( self, msg ):
        print 'tcp to %s:%d: %s' % (self.host, self.port, msg)

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
        while True:
            consumed = self.data_consumer(self.recv_buf)
            if not consumed: break
            assert consumed <= len(self.recv_buf), repr(consumed)
            self.recv_buf = self.recv_buf[consumed:]
            self.trace('consumed %d bytes, remained %d' % (consumed, len(self.recv_buf)))

    def send_data( self, contents ):
        data = encode_tcp_packet(contents)
        self.trace('sending data, old=%d, write=%d, new=%d' % (len(self.send_buf), len(data), len(self.send_buf) + len(data)))
        print '***', repr(data)
        if self.connected and not self.send_buf:
            self.socket.write(data)
        self.send_buf += data  # may be sent partially, will send remainder on bytesWritten signal

    def __del__( self ):
        print '~TcpConnection', self.host, self.port
