import datetime
import json
import struct
import socket
import pprint
import dateutil.parser


RECV_SIZE = 4096


class Error(Exception): pass


class JSONEncoder(json.JSONEncoder):

    def default( self, obj ):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


def json_decoder( obj ):
    if isinstance(obj, basestring):
        try:
            return dateutil.parser.parse(obj)  # will parse timezone too, if included
        except ValueError:
            return obj
    if isinstance(obj, list):
        return map(json_decoder, obj)
    if isinstance(obj, dict):
        return dict((json_decoder(key), json_decoder(value)) for key, value in obj.items())
    return obj


packet_size_struct_format = '>I'

def packet_size_size():
    return struct.calcsize(packet_size_struct_format)

def encode_packet_size( size ):
    return struct.pack(packet_size_struct_format, size)

def decode_packet_size( data ):
    return struct.unpack(packet_size_struct_format, data)[0]

def encode_packet( value ):
    json_data = json.dumps(value, cls=JSONEncoder)
    return encode_packet_size(len(json_data)) + json_data

def is_full_packet( data ):
    ssize = packet_size_size()
    if len(data) < ssize:
        return False
    data_size = decode_packet_size(data[:ssize])
    return len(data) >= ssize + data_size

def decode_packet( data ):
    assert is_full_packet(data)
    ssize = packet_size_size()
    data_size = decode_packet_size(data[:ssize])
    remainder = data[ssize + data_size:]
    json_data = json.loads(data[ssize:ssize + data_size], object_hook=json_decoder)
    return (json_data, remainder)


class Connection(object):

    def __init__( self, sock ):
        self.socket = sock
        self.recv_buf = ''

    def close( self ):
        self.socket.close()

    def send( self, value ):
        ## print 'send:'
        ## pprint.pprint(value)
        data = encode_packet(value)
        ofs = 0
        while ofs < len(data):
            sent_size = self.socket.send(data[ofs:])
            print '  sent (%d) %s' % (sent_size, data[ofs:ofs + sent_size])
            if sent_size == 0:
                raise Error('Socket is closed')
            ofs += sent_size

    def receive( self ):
        while True:
            ## print '  receiving...'
            chunk = self.socket.recv(RECV_SIZE)
            print '  received (%d): %s' % (len(chunk), chunk)
            if chunk == '':
                raise Error('Socket is closed')
            self.recv_buf += chunk
            if is_full_packet(self.recv_buf): break
        json_data, self.recv_buf = decode_packet(self.recv_buf)
        ## print 'received:'
        ## pprint.pprint(json_data)
        return json_data
                    
        
class Server(object):

    def __init__( self, port, server_fn ):
        self.port = port
        self.server_fn = server_fn
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.socket.listen(5)

    def run( self ):
        print 'listening on port %d' % self.port
        while True:
            cln_socket, cln_addr = self.socket.accept()
            self.server_fn(Connection(cln_socket), cln_addr)


class ClientConnection(Connection):
        
    def __init__( self, addr ):
        sock = socket.create_connection(addr)
        Connection.__init__(self, sock)
