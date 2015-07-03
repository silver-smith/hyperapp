import traceback
import pprint
import select
from Queue import Queue
from common.interface import iface_registry
from common.request import TRequest, ServerNotification, Response
from common.json_packet import encode_packet, is_full_packet, decode_packet
from common.json_decoder import JsonDecoder
from common.json_encoder import JsonEncoder
from module import Module


NOTIFICATION_DELAY_TIME = 1  # sec
RECV_SIZE = 4096


class Error(Exception): pass


class Connection(object):

    def __init__( self, socket ):
        self.socket = socket
        self.recv_buf = ''

    def close( self ):
        self.socket.close()

    def send( self, packet ):
        data = encode_packet(packet)
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
        self.updates_queue = Queue()  # Update queue

    def send_update( self, update ):
        self.updates_queue.put(update)

    def stop( self ):
        self.stop_flag = True

    def serve( self ):
        try:
            while not self.stop_flag:
                json_packet = self.conn.receive(NOTIFICATION_DELAY_TIME)
                if json_packet is None:
                    if not self.updates_queue.empty():
                        self._send_notification()
                    continue
                print '%s from %s:%d:' % ('request' if 'request_id' in json_packet else 'notification', self.addr[0], self.addr[1])
                pprint.pprint(json_packet)
                response = self._process_json_packet(json_packet)
                if response is not None:
                    print 'response to %s:%d:' % self.addr
                    response.pprint()
                    self.conn.send(response.encode(JsonEncoder()))
                else:
                    print 'no response'
        except Error as x:
            print x
        except:
            traceback.print_exc()
        self.conn.close()
        self.on_close(self)

    def _process_json_packet( self, json_packet ):
        path = json_packet['path']
        object = self._resolve(path)
        print 'Object:', object
        assert object, repr(path)  # 404: Path not found
        decoder = JsonDecoder(self, iface_registry)
        request = decoder.decode(TRequest(), json_packet)
        response = object.process_request(request)
        return self.prepare_response(request, response)

    def prepare_response( self, request, response ):
        if response is None and isinstance(request, Request):
            response = request.make_response()  # client need a response to cleanup waiting response handler
        if response is None and not self.updates_queue.empty():
            response = ServerNotification()
        while not self.updates_queue.empty():
            response.add_update(self.updates_queue.get())
        assert response is None or isinstance(response, Response), repr(response)
        return response

    def _send_notification( self ):
        notification = ServerNotification()
        while not self.updates_queue.empty():
            notification.add_update(self.updates_queue.get())
        json_packet = notification.as_json()
        print 'notification to %s:%d:' % self.addr
        pprint.pprint(json_packet)
        self.conn.send(json_packet)
        
    def _resolve( self, path ):
        return Module.run_resolve(path)
