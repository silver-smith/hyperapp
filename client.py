#!/usr/bin/env python

from json_connection import JsonClientConnection


SERVER_ADDR = ('localhost', 8888)


def main():
    connection = JsonClientConnection(SERVER_ADDR)
    request = dict(path='test/path')
    connection.send(request)
    response = connection.receive()
    print 'response = %r' % response


main()
