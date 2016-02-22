#!/usr/bin/env python

import argparse
from hyperapp.common.identity import Identity
from hyperapp.server.server import Server
from hyperapp.server.tcp_server import TcpServer

# self-registering modules:
import hyperapp.server.tcp_transport
import hyperapp.server.ponyorm_module
import hyperapp.server.fs
import hyperapp.server.article
import hyperapp.server.blog
import hyperapp.server.server_management
import hyperapp.server.module_list
import hyperapp.server.test_list
import hyperapp.server.test_text_object
import hyperapp.server.code_repository


DEFAULT_ADDR = 'localhost:8888'
ENDPOINT_FNAME = 'server.endpoint'


def parse_addr( addr ):
    host, port_str = addr.split(':')
    port = int(port_str)
    return (host, port)

def main():
    parser = argparse.ArgumentParser(description='Hyperapp server')
    parser.add_argument('identity_fpath', help='path to identity file')
    parser.add_argument('endpoint_fpath', default=ENDPOINT_FNAME, help='path to endpoint file, generated on server start')
    parser.add_argument('addr', nargs='?', help='address to listen at', default=DEFAULT_ADDR)
    parser.add_argument('--test-delay', type=float, help='artificial delay for handling requests, seconds')
    args = parser.parse_args()

    identity = Identity.load_from_file(args.identity_fpath)
    host, port = parse_addr(args.addr)
    server = Server(args.test_delay)
    tcp_server = TcpServer(server, identity, host, port)
    tcp_server.get_endpoint().save_to_file(args.endpoint_fpath)
    tcp_server.run()


main()
