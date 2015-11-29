#!/usr/bin/env python

import argparse
from hyperapp.common.identity import Identity
from hyperapp.server.server import TcpServer

# self-registering modules:
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


def main():
    parser = argparse.ArgumentParser(description='Hyperapp server')
    parser.add_argument('identity_fpath', help='path to identity file')
    parser.add_argument('addr', nargs='?', help='address to listen at', default=DEFAULT_ADDR)
    args = parser.parse_args()

    identity = Identity.load_from_file(args.identity_fpath)
    server = TcpServer(identity, args.addr)
    server.get_endpoint().save_to_file(ENDPOINT_FNAME)
    server.run()


main()
