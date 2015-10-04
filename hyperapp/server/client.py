import os.path
import traceback
import select
from Queue import Queue
from ..common.interface import ModuleDep, Module
from ..common.packet import tAuxInfo, AuxInfo, Packet
from ..common.interface import iface_registry
from ..common.request import tServerPacket, tClientPacket, ServerNotification, Request, Response, decode_client_packet
from ..common.requirements_collector import RequirementsCollector
from ..common.visual_rep import pprint
from .util import XPathNotFound
from . import module


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
                    self._wrap_and_send(packet.encoding, response)
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
        test_list_iface_module = self._load_module(
            '0df259a7-ca1c-43d5-b9fa-f787a7271db9', 'hyperapp.common.interface', 'common/interface/test_list.py')
        form_module = self._load_module('7e947453-84f3-44e9-961c-3e18fcdc37f0', 'hyperapp.client', 'client/form.py')
        return AuxInfo(
            requirements=requirements,
            modules=[form_module, test_list_iface_module])

    def _load_module( self, id, package, fpath ):
        fpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', fpath))
        with open(fpath) as f:
            source = f.read()
        return Module(id=id, package=package, deps=[], source=source, fpath=fpath)

    def _process_packet( self, packet ):
        request = packet.decode_client_packet(self, iface_registry)
        print '%r from %s:%d:' % (packet, self.addr[0], self.addr[1])
        pprint(tClientPacket, request)
        path = request.path
        object = self._resolve(path)
        print 'Object:', object
        assert object, repr(path)  # 404: Path not found
        response = object.process_request(request)
        return self.prepare_response(object.__class__, request, response)

    def prepare_response( self, obj_class, request, response ):
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
        notification = ServerNotification(self)
        while not self.updates_queue.empty():
            notification.add_update(self.updates_queue.get())
        self._send(PACKET_ENCODING, notification)
        
    def _resolve( self, path ):
        return module.Module.run_resolver(path)
