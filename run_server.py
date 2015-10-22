#!/usr/bin/env python

import argparse
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


def main():
    parser = argparse.ArgumentParser(description='Hyperapp server')
    parser.add_argument('addr', nargs='?', help='address to listen at', default=DEFAULT_ADDR)
    args = parser.parse_args()

    host, port = args.addr.split(':')
    server = TcpServer(host, int(port))
    server.run()


main()
