import traceback
import select
from Queue import Queue
from common.packet import Packet
from common.packet_coders import packet_coders
from common.interface import iface_registry
from common.request import tServerPacket, tClientPacket, ServerNotification, Request, Response
from common.visual_rep import pprint
from util import XPathNotFound
from module import Module


PACKET_ENCODING = 'cdr'
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
        data = packet.encode()
        ofs = 0
        while ofs < len(data):
            sent_size = self.socket.send(data[ofs:])
            print '  sent (%d) %s...' % (sent_size, data[ofs:ofs + min(sent_size, 100)])
            if sent_size == 0:
                raise Error('Socket is closed')
            ofs += sent_size

    def receive( self, timeout ):
        while True:
            if Packet.is_full(self.recv_buf): break
            ## print '  receiving...'
            rd, wr, xc = select.select([self.socket], [], [self.socket], timeout)
            if not rd and not xc:
                return None
            chunk = self.socket.recv(RECV_SIZE)
            print '  received (%d) %s...' % (len(chunk), chunk[:100])
            if chunk == '':
                raise Error('Socket is closed')
            self.recv_buf += chunk
        packet, self.recv_buf = Packet.decode(self.recv_buf)
        ## print 'received:'
        ## pprint.pprint(json_data)
        return packet


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
                packet = self.conn.receive(NOTIFICATION_DELAY_TIME)
                if not packet:
                    if not self.updates_queue.empty():
                        self._send_notification()
                    continue
                response = self._process_packet(packet)
                if response is not None:
                    self._send(packet.encoding, response)
                else:
                    print 'no response'
        except Error as x:
            print x
        except:
            traceback.print_exc()
        self.conn.close()
        self.on_close(self)

    def _send( self, encoding, response_or_notification ):
        packet = packet_coders.encode(encoding, response_or_notification, tServerPacket)
        print '%s packet to %s:%d:' % (packet.encoding, self.addr[0], self.addr[1])
        pprint(tServerPacket, response_or_notification)
        self.conn.send(packet)

    def _process_packet( self, packet ):
        request = packet_coders.decode(packet, tClientPacket, self, iface_registry)
        print '%s packet from %s:%d:' % (packet.encoding, self.addr[0], self.addr[1])
        pprint(tClientPacket, request)
        path = request.path
        object = self._resolve(path)
        print 'Object:', object
        assert object, repr(path)  # 404: Path not found
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
        notification = ServerNotification(self)
        while not self.updates_queue.empty():
            notification.add_update(self.updates_queue.get())
        self._send(PACKET_ENCODING, notification)
        
    def _resolve( self, path ):
        return Module.run_resolver(path)
