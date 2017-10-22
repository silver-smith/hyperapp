import sys
import time
import logging
import threading
import socket
import select
import traceback
from .module import Module
from .tcp_client import TcpClient

log = logging.getLogger(__name__)


#TRANSPORT_ID = 'tcp.cdr'
TRANSPORT_ID = 'encrypted_tcp'
STOP_DELAY_TIME_SEC = 0.3


def parse_addr(addr):
    host, port_str = addr.split(':')
    port = int(port_str)
    return (host, port)
          

class TcpServer(object):

    @classmethod
    def create(cls, services, start_args):
        host, port = parse_addr(start_args.addr)
        return cls(
            services.remoting,
            services.server,
            host,
            port,
            )

    def __init__(self, remoting, server, host, port):
        self._remoting = remoting
        self._server = server
        self._host = host
        self._port = port
        self._listen_thread = threading.Thread(target=self._main)
        self._client2thread = {}  # client -> thread
        self._stop_flag = False
        self._finished_threads = []
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._host, self._port))
        self._socket.listen(5)
        log.info('listening on %s:%d', self._host, self._port)

    def get_routes(self):
        route = [TRANSPORT_ID, self._host, str(self._port)]
        return [route]

    @property
    def is_running(self):
        return not self._stop_flag

    def start(self):
        self._listen_thread.start()

    def stop(self):
        log.info('Stopping tcp server...')
        self._stop_flag = True
        for client in self._client2thread.keys():
            client.stop()
        while self._client2thread:
            time.sleep(0.1)  # hacky
        self._join_finished_threads()
        self._listen_thread.join()
        log.info('Tcp server is stopped.')

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
                client = TcpClient(self._remoting, self._server, self, cln_socket, cln_addr, on_close=self._on_client_closed)
                thread = threading.Thread(target=client.serve)
                thread.start()
                self._client2thread[client] = thread
            self._join_finished_threads()

    def _join_finished_threads(self):
        for thread in self._finished_threads:
            thread.join()
        self._finished_threads = []

    # called from client thread
    def _on_client_closed(self, client):
        self._finished_threads.append(self._client2thread[client])
        del self._client2thread[client]
        log.info('client %s:%d is gone' % client.get_addr())
