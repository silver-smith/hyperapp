import os.path
import traceback
import time
import select
from ..common.htypes import iface_registry
from ..common.interface.code_repository import ModuleDep
from ..common.transport_packet import encode_transport_packet, decode_transport_packet
from ..common.tcp_packet import has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet
from .transport import transport_registry
from .transport_session import TransportSessionList


PACKET_ENCODING = 'cdr'
NOTIFICATION_DELAY_TIME = 1  # sec
RECV_SIZE = 4096


class Error(Exception): pass


class TcpConnection(object):

    def __init__( self, socket ):
        self.socket = socket
        self.recv_buf = ''

    def close( self ):
        self.socket.close()

    def send( self, contents ):
        data = encode_tcp_packet(contents)
        ofs = 0
        while ofs < len(data):
            sent_size = self.socket.send(data[ofs:])
            print '  sent (%d) %s...' % (sent_size, data[ofs:ofs + min(sent_size, 100)])
            if sent_size == 0:
                raise Error('Socket is closed')
            ofs += sent_size

    def receive( self, timeout ):
        while not has_full_tcp_packet(self.recv_buf):
            ## print '  receiving...'
            rd, wr, xc = select.select([self.socket], [], [self.socket], timeout)
            if not rd and not xc:
                return None
            chunk = self.socket.recv(RECV_SIZE)
            print '  received (%d) %s...' % (len(chunk), chunk[:100])
            if chunk == '':
                raise Error('Socket is closed')
            self.recv_buf += chunk
        packet_data, packet_size = decode_tcp_packet(self.recv_buf)
        self.recv_buf = self.recv_buf[packet_size:]
        ## print 'received:'
        ## pprint.pprint(json_data)
        return packet_data


class TcpClient(object):

    def __init__( self, server, tcp_server, socket, addr, on_close ):
        self.server = server
        self.tcp_server = tcp_server
        self.conn = TcpConnection(socket)
        self.addr = addr
        self.on_close = on_close
        self.stop_flag = False
        self.session_list = TransportSessionList()

    def send_update( self, update ):
        self.updates_queue.put(update)

    def stop( self ):
        self.stop_flag = True

    def serve( self ):
        try:
            while not self.stop_flag:
                packet_data = self.conn.receive(NOTIFICATION_DELAY_TIME)
                if not packet_data:  # receive timed out
                    for transport_packet in self.session_list.pull_notification_transport_packets():
                        self._send_notification(transport_packet)
                    continue
                self._process_packet(packet_data)
        except Error as x:
            print x
        except:
            traceback.print_exc()
        self.conn.close()
        self.on_close(self)

    def _process_packet( self, request_data ):
        request_packet = decode_transport_packet(request_data)
        print '%r packet from %s:%d:' % (request_packet.transport_id, self.addr[0], self.addr[1])
        response_packet = transport_registry.process_packet(iface_registry, self.server, self.session_list, request_packet)
        if response_packet is None:
            print 'no response'
            return None
        print '%d bytes to %s:%d' % (len(response_packet.data), self.addr[0], self.addr[1])
        response_data = encode_transport_packet(response_packet)
        self.conn.send(response_data)

    def _send_notification( self, transport_packet ):
        print '%d bytes to %s:%d' % (len(transport_packet.data), self.addr[0], self.addr[1])
        data = encode_transport_packet(transport_packet)
        self.conn.send(data)
