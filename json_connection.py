import json
import struct
import socket


RECV_SIZE = 4096


class JsonConnection(object):

    size_struct_format = '>I'

    def __init__( self, sock ):
        self.socket = sock

    def close( self ):
        self.socket.close()

    def size_data_size( self ):
        return struct.calcsize(self.size_struct_format)

    def encode_size( self, size ):
        return struct.pack(self.size_struct_format, size)

    def decode_size( self, data ):
        return struct.unpack(self.size_struct_format, data)[0]

    def send( self, value ):
        json_data = json.dumps(value)
        data = self.encode_size(len(json_data)) + json_data
        ofs = 0
        while ofs < len(data):
            sent_size = self.socket.send(data[ofs:])
            print 'sent (%d) %s' % (sent_size, data[ofs:ofs + sent_size])
            if sent_size == 0:
                raise RuntimeError('Socket is closed')
            ofs += sent_size

    def receive( self ):
        data_size = None
        data = ''
        while data_size is None or len(data) < data_size:
            data += self.socket.recv(RECV_SIZE)
            print 'received (%d): %s' % (len(data), data)
            if data_size is not None: continue
            ssize = self.size_data_size()
            if len(data) < ssize: continue
            data_size = self.decode_size(data[:ssize])
            data = data[ssize:]
        return data
                    
        
class JsonServer(object):

    def __init__( self, port, server_fn ):
        self.server_fn = server_fn
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', port))
        self.socket.listen(5)

    def run( self ):
        while True:
            cln_socket, cln_addr = self.socket.accept()
            self.server_fn(JsonConnection(cln_socket), cln_addr)


class JsonClientConnection(JsonConnection):
        
    def __init__( self, addr ):
        sock = socket.create_connection(addr)
        JsonConnection.__init__(self, sock)
