import sys
import time
import logging
import threading
import socket
import select
from ..common.endpoint import Endpoint
from .module import Module
from .tcp_client import TcpClient

log = logging.getLogger(__name__)


#TRANSPORT_ID = 'tcp.cdr'
TRANSPORT_ID = 'encrypted_tcp'
          

class TcpServer(object):

    def __init__( self, server, host, port ):
        self.server = server
        self.host = host
        self.port = port
        self.client2thread = {}  # client -> thread
        self.finished_threads = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        log.info('listening on port %s:%d', self.host, self.port)

    def get_endpoint( self ):
        route = [TRANSPORT_ID, self.host, str(self.port)]
        return Endpoint(self.server.get_public_key(), [route])

    def run( self ):
        Module.init_phases()
        try:
            self.accept_loop()
        except KeyboardInterrupt:
            log.info()
            log.info('Stopping...')
            self.stop()
        log.info('Stopped')

    def accept_loop( self ):
        while True:
            select.select([self.socket], [], [self.socket])
            cln_socket, cln_addr = self.socket.accept()
            log.info('accepted connection from %s:%d' % cln_addr)
            client = TcpClient(self.server, self, cln_socket, cln_addr, on_close=self.on_client_closed)
            thread = threading.Thread(target=client.serve)
            thread.start()
            self.client2thread[client] = thread
            self.join_finished_threads()

    def stop( self ):
        for client in self.client2thread.keys():
            client.stop()
        while self.client2thread:
            time.sleep(0.1)  # hacky
        self.join_finished_threads()

    def join_finished_threads( self ):
        for thread in self.finished_threads:
            thread.join()
        self.finished_threads = []

    # called from client thread
    def on_client_closed( self, client ):
        self.finished_threads.append(self.client2thread[client])
        del self.client2thread[client]
        log.info('client %s:%d is gone' % client.addr)
