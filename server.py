#!/usr/bin/env python

from json_connection import JsonServer


LISTEN_PORT = 8888


def server_fn( connection, cln_addr ):
    print 'accepted connection from %s:%d' % cln_addr
    request = connection.receive()
    print 'request: %r' % request
    response = dict(result='ok')
    connection.send(response)


def main():
    server = JsonServer(LISTEN_PORT, server_fn)
    server.run()


main()
