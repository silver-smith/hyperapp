from PySide import QtNetwork
import json_connection
import proxy_registry
import view_registry
from proxy_object import ProxyListObject


def resolve_handle( server, resp ):
    iface_id = resp['iface_id']
    path = resp['path']
    obj_ctr = proxy_registry.resolve_iface(iface_id)
    object = obj_ctr(server, resp)
    view_id = resp['view_id']
    handle_ctr = view_registry.resolve_view(view_id)
    return handle_ctr(object, resp)


class ListDiff(object):

    @classmethod
    def from_resp( cls, d ):
        return cls(
            start_key=d['start_key'],
            end_key=d['end_key'],
            elements=[ProxyListObject.element_from_json(elt) for elt in d['elements']],
            )

    def __init__( self, start_key, end_key, elements ):
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (but not including) this one
        self.elements = elements    # with these elemenents


class ResultDict(object):

    def __init__( self, d ):
        self._d = d

    def __getattr__( self, attr ):
        return self._d[attr]


class Response(object):

    def __init__( self, server, resp_dict ):
        self.server = server
        self.resp_dict = resp_dict
        self.request_id = self.resp_dict['request_id']

    @property
    def result( self ):
        if 'result' in self.resp_dict:
            return ResultDict(self.resp_dict['result'])

    def get_updates( self ):
        if 'updates' not in self.resp_dict:
            return []
        return [(path, ListDiff.from_resp(diff)) for path, diff in self.resp_dict['updates']]

    def get_handle2open( self ):
        if 'object' in self.resp_dict:
            return resolve_handle(self.server, self.resp_dict['object'])
        else:
            return None


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
        print 'Network, connection to %s:%d: %s' % (host, port, msg)

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
        self.trace('%d bytes is received: %s' % (len(data), data))
        self.recv_buf += data
        while json_connection.is_full_packet(self.recv_buf):
            value, self.recv_buf = json_connection.decode_packet(self.recv_buf)
            self.trace('received packet (%d bytes remainder): %s' % (len(self.recv_buf), value))
            self.process_packet(value)
            
    def process_packet( self, value ):
        print 'processing packet:', value
        response = Response(Server(self.addr), value)
        proxy_registry.process_received_packet(response)

    def send_data( self, data ):
        self.trace('sending data, old=%d, write=%d, new=%d' % (len(self.send_buf), len(data), len(self.send_buf) + len(data)))
        if self.connected and not self.send_buf:
            self.socket.write(data)
        self.send_buf += data  # may be sent partially, will send remainder on bytesWritten signal

    def __del__( self ):
        print '~Connection', self.addr


class Server(object):

    def __init__( self, addr ):
        self.addr = addr

    def execute_request( self, request, resp_handler ):
        request_id = request['request_id']
        print 'execute_request', request_id, request
        proxy_registry.register_resp_handler(request_id, resp_handler)
        data = json_connection.encode_packet(request)
        Connection.get_connection(self.addr).send_data(data)
