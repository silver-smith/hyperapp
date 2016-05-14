#!/usr/bin/env python

import logging
import argparse
from hyperapp.common.identity import Identity
from hyperapp.server.server import Server
from hyperapp.server.tcp_server import TcpServer
from hyperapp.server.server_management import get_management_url

log = logging.getLogger(__name__)

# self-registering modules:
import hyperapp.server.tcp_transport
import hyperapp.server.encrypted_transport
import hyperapp.server.ponyorm_module
import hyperapp.server.fs
import hyperapp.server.article
import hyperapp.server.blog
import hyperapp.server.server_management
import hyperapp.server.admin
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
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s  %(message)s')

    parser = argparse.ArgumentParser(description='Hyperapp server')
    parser.add_argument('identity_fpath', help='path to identity file')
    parser.add_argument('addr', nargs='?', help='address to listen at', default=DEFAULT_ADDR)
    parser.add_argument('--test-delay', type=float, help='artificial delay for handling requests, seconds')
    args = parser.parse_args()

    identity = Identity.load_from_file(args.identity_fpath)
    host, port = parse_addr(args.addr)
    server = Server(identity, args.test_delay)
    tcp_server = TcpServer(server, host, port)
    management_url = get_management_url(tcp_server.get_endpoint())
    log.info('Management url:%s', management_url.to_str())
    tcp_server.run()


main()
