#!/usr/bin/env python3

import logging
import argparse
from hyperapp.common.identity import Identity
from hyperapp.server.services import Services
from hyperapp.server.server import Server
from hyperapp.server.tcp_server import TcpServer
from hyperapp.server.server_management import get_management_url

log = logging.getLogger(__name__)

# self-registering modules:
import hyperapp.server.ponyorm_module
import hyperapp.server.server_management


DEFAULT_ADDR = 'localhost:8888'


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
    services = Services()
    server = Server(identity, args.test_delay)
    tcp_server = TcpServer(services.remoting, server, host, port)
    management_url = get_management_url(server.get_public_key())
    url_with_routes = management_url.clone_with_routes(tcp_server.get_routes())
    log.info('Management url: %s', url_with_routes.to_str())
    tcp_server.run()


main()
