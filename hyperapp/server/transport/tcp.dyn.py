import logging
import threading
import socket
import select
import traceback

from hyperapp.common.interface import tcp_transport as tcp_transport_types
from hyperapp.common.ref import make_object_ref
from ..module import Module

log = logging.getLogger(__name__)


LISTEN_HOST = 'localhost'
LISTEN_PORT = 9999
STOP_DELAY_TIME_SEC = 0.3

MODULE_NAME = 'transport.tcp'


class Server(object):

    def __init__(self, bind_address):
        self._bind_address = bind_address  # (host, port)
        self._listen_thread = threading.Thread(target=self._main)
        self._stop_flag = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(self._bind_address)
        self._socket.listen(5)
        log.info('Tcp transport: listening on %s:%d' % self._bind_address)

    def start(self):
        self._listen_thread.start()

    def stop(self):
        log.info('Stopping tcp transport...')
        self._stop_flag = True
        self._listen_thread.join()
        log.info('Tcp transport is stopped.')

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
                cln_socket, cln_addr = self._socket.accept()
                log.info('accepted connection from %s:%d' % cln_addr)
                assert 0, cln_addr
                client = TcpClient(self._remoting, self._server, self, cln_socket, cln_addr, on_close=self._on_client_closed)
                thread = threading.Thread(target=client.serve)
                thread.start()
                self._client2thread[client] = thread
            #self._join_finished_threads()


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        self.server = Server(bind_address=(LISTEN_HOST, LISTEN_PORT))
        address = tcp_transport_types.address(LISTEN_HOST, LISTEN_PORT)
        services.tcp_transport_ref = services.ref_registry.register_object(tcp_transport_types.address, address)
        services.on_start.append(self.server.start)
        services.on_stop.append(self.server.stop)
