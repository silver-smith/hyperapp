import traceback
import pprint
import select
from json_packet import encode_packet, is_full_packet, decode_packet
from module import Module
from object import Response, Request


NOTIFICATION_DELAY_TIME = 1  # sec
RECV_SIZE = 4096


class Error(Exception): pass


class Connection(object):

    def __init__( self, socket ):
        self.socket = socket
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

    def receive( self, timeout ):
        while True:
            if is_full_packet(self.recv_buf): break
            ## print '  receiving...'
            rd, wr, xc = select.select([self.socket], [], [self.socket], timeout)
            if not rd and not xc:
                return None
            chunk = self.socket.recv(RECV_SIZE)
            print '  received (%d): %s' % (len(chunk), chunk)
            if chunk == '':
                raise Error('Socket is closed')
            self.recv_buf += chunk
        json_data, self.recv_buf = decode_packet(self.recv_buf)
        ## print 'received:'
        ## pprint.pprint(json_data)
        return json_data


class Client(object):

    def __init__( self, socket, addr, on_close ):
        self.conn = Connection(socket)
        self.addr = addr
        self.on_close = on_close
        self.stop_flag = False

    def stop( self ):
        self.stop_flag = True

    def serve( self ):
        try:
            while not self.stop_flag:
                json_packet = self.conn.receive(NOTIFICATION_DELAY_TIME)
                if json_packet is None: continue
                print 'request:' if 'request_id' in json_packet else 'notification:'
                pprint.pprint(json_packet)
                request = Request(self, json_packet)
                response = self.process_request(request)
                if response is not None:
                    json_response = response.as_json()
                    print 'response:'
                    pprint.pprint(json_response)
                    self.conn.send(json_response)
                else:
                    print 'no response'
        except Error as x:
            print x
        except:
            traceback.print_exc()
        self.conn.close()
        self.on_close(self)

    def process_request( self, request ):
        object = self.resolve(request.path)
        print 'Object:', object
        assert object, repr(request.path)  # 404: Path not found
        response = object.process_request(request)
        if response is None and request.is_response_needed():
            response = request.make_response()  # client need a response to cleanup waiting response handler
        assert response is None or isinstance(response, Response), repr(response)
        return response

    def resolve( self, path ):
        return Module.run_resolve(path)
