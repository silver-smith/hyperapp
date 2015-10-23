import sys
import time
import threading
import socket
import select
from .module import Module
from .client import Client
          

class TcpServer(object):

    def __init__( self, addr ):
        self.addr = addr
        host, port_str = addr.split(':')
        port = int(port_str)
        self.client2thread = {}  # client -> thread
        self.finished_threads = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(5)
        print 'listening on port %s:%d' % (host, port)

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
