import os.path
import traceback
import time
import select
from Queue import Queue
from ..common.htypes import tServerPacket
from ..common.interface.code_repository import ModuleDep
from ..common.packet import tAuxInfo, AuxInfo, Packet
from ..common.htypes import tClientPacket, iface_registry
from ..common.requirements_collector import RequirementsCollector
from ..common.object_path_collector import ObjectPathCollector
from ..common.visual_rep import pprint
from .util import XPathNotFound
from .request import RequestBase, Request, ServerNotification, Response
from .object import subscription
from . import module
from .code_repository import code_repository


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
            if Packet.has_full_packet(self.recv_buf): break
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

    def __init__( self, server, socket, addr, test_delay_sec, on_close ):
        self.server = server
        self.conn = Connection(socket)
        self.addr = addr
        self.test_delay_sec = test_delay_sec  # float
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
                    self._wrap_and_send(packet.encoding, response.encode())
                else:
                    print 'no response'
        except Error as x:
            print x
        except:
            traceback.print_exc()
        self.conn.close()
        self.on_close(self)

    def _wrap_and_send( self, encoding, response_or_notification ):
        aux = self._prepare_aux_info(response_or_notification)
        packet = Packet.from_contents(encoding, response_or_notification, tServerPacket, aux)
        print '%r to %s:%d:' % (packet, self.addr[0], self.addr[1])
        pprint(tAuxInfo, aux)
        pprint(tServerPacket, response_or_notification)
        self.conn.send(packet)

    def _prepare_aux_info( self, response_or_notification ):
        requirements = RequirementsCollector().collect(tServerPacket, response_or_notification)
        modules = code_repository.get_required_modules(requirements)
        modules = []  # force separate request to code repository
        return AuxInfo(
            requirements=requirements,
            modules=modules)

    def _process_packet( self, packet ):
        request_rec = packet.decode_client_packet()
        print '%r from %s:%d:' % (packet, self.addr[0], self.addr[1])
        pprint(tClientPacket, request_rec)
        request = RequestBase.from_request_rec(self.server, self, iface_registry, request_rec)
        path = request.path
        object = self._resolve(path)
        print 'Object:', object
        assert object, repr(path)  # 404: Path not found
        if self.test_delay_sec:
            print 'Test delay for %s sec...' % self.test_delay_sec
            time.sleep(self.test_delay_sec)
        response = object.process_request(request)
        if response:
            self._subscribe_objects(response)
        return self._prepare_response(object.__class__, request, response)

    def _subscribe_objects( self, response ):
        collector = ObjectPathCollector()
        object_paths = collector.collect(tServerPacket, response.encode())
        for path in object_paths:
            subscription.add(path, self)

    def _prepare_response( self, obj_class, request, response ):
        if response is None and isinstance(request, Request):
            response = request.make_response()  # client need a response to cleanup waiting response handler
        if response is None and not self.updates_queue.empty():
            response = ServerNotification()
        while not self.updates_queue.empty():
            response.add_update(self.updates_queue.get())
        assert response is None or isinstance(response, Response), \
          'Server commands must return a response, but %s.%s command returned %r' % (obj_class.__name__, request.command_id, response)
        return response

    def _send_notification( self ):
        notification = ServerNotification()
        while not self.updates_queue.empty():
            notification.add_update(self.updates_queue.get())
        self._wrap_and_send(PACKET_ENCODING, notification.encode())
        
    def _resolve( self, path ):
        return module.Module.run_resolver(path)
