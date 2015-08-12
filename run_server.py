#!/usr/bin/env python

from server.server import TcpServer

# self-registering modules:
import server.ponyorm_module
import server.fs
import server.article
import server.blog
import server.server_management
import server.test_list


LISTEN_PORT = 8888


def main():
    server = TcpServer(LISTEN_PORT)
    server.run()


main()
