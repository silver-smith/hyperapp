import os.path
import logging
import traceback
import time
import select
from ..common.transport_packet import encode_transport_packet, decode_transport_packet
from ..common.tcp_packet import has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet
from .transport_session import TransportSessionList

log = logging.getLogger(__name__)


NOTIFICATION_DELAY_TIME = 1  # sec
RECV_SIZE = 4096


class Error(Exception): pass


class TcpConnection(object):

    def __init__(self, socket):
        self.socket = socket
        self.recv_buf = b''

    def close(self):
        self.socket.close()

    def send(self, contents):
        data = encode_tcp_packet(contents)
        ofs = 0
        while ofs < len(data):
            sent_size = self.socket.send(data[ofs:])
            log.info('  sent (%d) %s...', sent_size, data[ofs:ofs + min(sent_size, 100)])
            if sent_size == 0:
                raise Error('Socket is closed')
            ofs += sent_size

    def receive(self, timeout):
        while not has_full_tcp_packet(self.recv_buf):
            ## print '  receiving...'
            rd, wr, xc = select.select([self.socket], [], [self.socket], timeout)
            if not rd and not xc:
                return None
            chunk = self.socket.recv(RECV_SIZE)
            log.info('  received (%d) %s...', len(chunk), chunk[:100])
            if chunk == b'':
                raise Error('Socket is closed')
            self.recv_buf += chunk
        packet_data, packet_size = decode_tcp_packet(self.recv_buf)
        self.recv_buf = self.recv_buf[packet_size:]
        ## print 'received:'
        ## pprint.pprint(json_data)
        return packet_data


class TcpClient(object):

    def __init__(self, remoting, server, tcp_server, socket, addr, on_close):
        self._remoting = remoting
        self._server = server
        #self.tcp_server = tcp_server
        self._connection = TcpConnection(socket)
        self._addr = addr
        self._on_close = on_close
        self._stop_flag = False
        self._session_list = TransportSessionList()

    def get_addr(self):
        return self._addr

    def send_update(self, update):
        self.updates_queue.put(update)

    def stop(self):
        self._stop_flag = True

    def serve(self):
        try:
            while not self._stop_flag:
                packet_data = self._connection.receive(NOTIFICATION_DELAY_TIME)
                if not packet_data:  # receive timed out
                    for transport_packet in self._session_list.pull_notification_transport_packets():
                        log.info('sending %r notification:', transport_packet.transport_id)
                        self._send_notification(transport_packet)
                    continue
                self._process_packet(packet_data)
        except Error as x:
            log.info('Error: %r', x)
        except:
            traceback.print_exc()
        self._connection.close()
        self._on_close(self)

    def _process_packet(self, request_data):
        request_packet = decode_transport_packet(request_data)
        log.info('%r packet from %s:%d:', request_packet.transport_id, self._addr[0], self._addr[1])
        response_packets = self._remoting.process_packet(self._remoting.iface_registry, self._server, self._session_list, request_packet)
        if not response_packets:
            log.info('no response')
        for response_packet in response_packets:
            log.info('response: %d bytes to %s:%d', len(response_packet.data), self._addr[0], self._addr[1])
            response_data = encode_transport_packet(response_packet)
            self._connection.send(response_data)

    def _send_notification(self, transport_packet):
        log.info('%d bytes to %s:%d', len(transport_packet.data), self._addr[0], self._addr[1])
        data = encode_transport_packet(transport_packet)
        self._connection.send(data)
