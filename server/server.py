#!/usr/bin/env python

import sys
import time
import threading
import socket
import select

sys.path.append('..')

from module import Module
from client import Client

# self-registering modules:
import ponyorm_module
import fs
import article
import blog
import server_management
import test_list


LISTEN_PORT = 8888
          

class TcpServer(object):

    def __init__( self, port ):
        self.port = port
        self.client2thread = {}  # client -> thread
        self.finished_threads = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.socket.listen(5)
        print 'listening on port %d' % self.port

    def run( self ):
        while True:
            select.select([self.socket], [], [self.socket])
            cln_socket, cln_addr = self.socket.accept()
            print 'accepted connection from %s:%d' % cln_addr
            client = Client(cln_socket, cln_addr, on_close=self.on_client_closed)
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
        print 'client %s:%d is finished' % client.addr


def main():
    Module.init_phases()
    server = TcpServer(LISTEN_PORT)
    try:
        server.run()
    except KeyboardInterrupt:
        print
        print 'Stopping...'
        server.stop()
    print 'Stopped'


main()
