import sys
import time
import logging
import threading
import socket
import select
from .module import Module
from .tcp_client import TcpClient

log = logging.getLogger(__name__)


#TRANSPORT_ID = 'tcp.cdr'
TRANSPORT_ID = 'encrypted_tcp'
          

class TcpServer(object):

    def __init__(self, remoting, server, host, port):
        self._remoting = remoting
        self._server = server
        self._host = host
        self._port = port
        self._client2thread = {}  # client -> thread
        self._finished_threads = []
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._host, self._port))
        self._socket.listen(5)
        log.info('listening on %s:%d', self._host, self._port)

    def get_routes(self):
        route = [TRANSPORT_ID, self._host, str(self._port)]
        return [route]

    def run(self):
        try:
            self.accept_loop()
        except KeyboardInterrupt:
            log.info('Stopping...')
            self.stop()
        log.info('Stopped')

    def accept_loop(self):
        while True:
            select.select([self._socket], [], [self._socket])
            cln_socket, cln_addr = self._socket.accept()
            log.info('accepted connection from %s:%d' % cln_addr)
            client = TcpClient(self._remoting, self._server, self, cln_socket, cln_addr, on_close=self.on_client_closed)
            thread = threading.Thread(target=client.serve)
            thread.start()
            self._client2thread[client] = thread
            self.join_finished_threads()

    def stop(self):
        for client in self._client2thread.keys():
            client.stop()
        while self._client2thread:
            time.sleep(0.1)  # hacky
        self.join_finished_threads()

    def join_finished_threads(self):
        for thread in self._finished_threads:
            thread.join()
        self._finished_threads = []

    # called from client thread
    def on_client_closed(self, client):
        self._finished_threads.append(self._client2thread[client])
        del self._client2thread[client]
        log.info('client %s:%d is gone' % client.get_addr())
