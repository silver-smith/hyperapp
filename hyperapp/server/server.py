import sys
import time
import threading
import socket
import select
from ..common.identity import Identity
from ..common.endpoint import Endpoint
from .module import Module
from .client import Client
          

class TcpServer(object):

    def __init__( self, identity, host, port ):
        assert isinstance(identity, Identity), repr(identity)
        self.identity = identity
        self.host = host
        self.port = port
        self.client2thread = {}  # client -> thread
        self.finished_threads = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        print 'listening on port %s:%d' % (self.host, self.port)

    def get_endpoint( self ):
        route = ['tcp', self.host, str(self.port)]
        return Endpoint(self.identity.get_public_key(), [route])

    def run( self ):
        Module.init_phases()
        try:
            self.accept_loop()
        except KeyboardInterrupt:
            print
            print 'Stopping...'
            self.stop()
        print 'Stopped'

    def accept_loop( self ):
        while True:
            select.select([self.socket], [], [self.socket])
            cln_socket, cln_addr = self.socket.accept()
            print 'accepted connection from %s:%d' % cln_addr
            client = Client(self, cln_socket, cln_addr, on_close=self.on_client_closed)
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

    def on_client_closed( self, client ):
        self.finished_threads.append(self.client2thread[client])
        del self.client2thread[client]
        print 'client %s:%d is gone' % client.addr

    def is_mine_url( self, url ):
        return url[0] == self.addr

    # split into transport/server and local path parts
    def split_url( self, url ):
        return (url[:1], url[1:])

    def make_url( self, path ):
        return [self.addr] + path
