import logging
import threading
import socket
import select
import time
import traceback

from hyperapp.common.interface import tcp_transport as tcp_transport_types
from hyperapp.common.ref import make_object_ref
from hyperapp.common.tcp_packet import has_full_tcp_packet, encode_tcp_packet, decode_tcp_packet

from ..module import Module

log = logging.getLogger(__name__)


DEFAULT_BIND_ADDRESS = ('localhost', 9999)
STOP_DELAY_TIME_SEC = 0.3
NOTIFICATION_DELAY_TIME_SEC = 1
RECV_SIZE = 4096

MODULE_NAME = 'transport.tcp'


class SocketClosedError(Exception):

    def __init__(self):
        super().__init__('Socket is closed by remote peer')


class TcpChannel(object):

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
                raise SocketClosedError()
            ofs += sent_size

    def receive(self, timeout_sec):
        while not has_full_tcp_packet(self.recv_buf):
            ## print '  receiving...'
            rd, wr, xc = select.select([self.socket], [], [self.socket], timeout_sec)
            if not rd and not xc:
                return None
            chunk = self.socket.recv(RECV_SIZE)
            log.info('  received (%d) %s...', len(chunk), chunk[:100])
            if chunk == b'':
                raise SocketClosedError()
            self.recv_buf += chunk
        bundle, packet_size = decode_tcp_packet(self.recv_buf)
        self.recv_buf = self.recv_buf[packet_size:]
        return bundle


class TcpClient(object):

    def __init__(self, remoting, tcp_server, peer_address, socket, on_failure):
        self._remoting = remoting
        self._tcp_server = tcp_server
        self._peer_address = peer_address
        self._channel = TcpChannel(socket)
        self._stop_flag = False
        self._thread = threading.Thread(target=self._thread_main)
        self._on_failure = on_failure

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_flag = True

    def join(self):
        self._thread.join()

    def _thread_main(self):
        self._log('started')
        try:
            while not self._stop_flag:
                self._receive_and_process_bundle()
        except SocketClosedError:
            self._log('connection is closed by remote peer')
        except Exception as x:
            traceback.print_exc()
            self._on_failure('Tcp client thread is failed: %r' % x)
        self._channel.close()
        self._tcp_server.client_finished(self)
        self._log('finished')

    def _receive_and_process_bundle(self):
        bundle = self._channel.receive(NOTIFICATION_DELAY_TIME_SEC)
        if bundle:  # receive timed out otherwise
            self._remoting.process_incoming_bundle(bundle)

    def _log(self, message, *args):
        log.info('tcp: client %s:%d: %s' % (self._peer_address[0], self._peer_address[1], message), *args)


class TcpServer(object):

    def __init__(self, remoting, bind_address, on_failure):
        self._remoting = remoting
        self._bind_address = bind_address  # (host, port)
        self._on_failure = on_failure
        self._listen_thread = threading.Thread(target=self._main)
        self._stop_flag = False
        self._client_set = set()
        self._finished_client_set = set()
        self._client_lock = threading.Lock()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(self._bind_address)
        self._socket.listen(5)
        log.info('Tcp transport: listening on %s:%d' % self._bind_address)

    def start(self):
        self._listen_thread.start()

    def stop(self):
        if self._stop_flag:
            log.info('tcp: already stopping')
            return
        log.info('tcp: stopping...')
        self._stop_flag = True
        self._listen_thread.join()
        for client in self._client_set:
            client.stop()
        while True:
            with self._client_lock:
                if not self._client_set:
                    break
            self._join_finished_clients()
            time.sleep(0.1)
        log.info('tcp: stopped.')

    def client_finished(self, client):
        with self._client_lock:
            assert client in self._client_set
            self._finished_client_set.add(client)

    def _main(self):
        try:
            self._accept_loop()
        except:
            traceback.print_exc()
            self._stop_flag = True

    def _accept_loop(self):
        while not self._stop_flag:
            rd, wr, err = select.select([self._socket], [], [self._socket], STOP_DELAY_TIME_SEC)
            if rd or err:
                channel_socket, peer_address = self._socket.accept()
                log.info('tcp: accepted connection from %s:%d' % peer_address)
                client = TcpClient(self._remoting, self, peer_address, channel_socket, self._on_failure)
                client.start()
                self._client_set.add(client)
            self._join_finished_clients()

    def _join_finished_clients(self):
        with self._client_lock:
            for client in self._finished_client_set:
                client.join()
                self._client_set.remove(client)
            self._finished_client_set.clear()


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        config = services.config.get(MODULE_NAME)
        bind_address = None
        if config:
            bind_address = config.get('bind_address')
        if not bind_address:
            bind_address = DEFAULT_BIND_ADDRESS
        self.server = TcpServer(services.remoting, bind_address=bind_address, on_failure=services.failed)
        address = tcp_transport_types.address(bind_address[0], bind_address[1])
        services.tcp_transport_ref = services.ref_registry.register_object(tcp_transport_types.address, address)
        services.on_start.append(self.server.start)
        services.on_stop.append(self.server.stop)
