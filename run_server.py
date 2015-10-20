#!/usr/bin/env python

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


LISTEN_PORT = 8888


def main():
    server = TcpServer(LISTEN_PORT)
    server.run()


main()
