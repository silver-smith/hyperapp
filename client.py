#!/usr/bin/env python

import json_connection


SERVER_ADDR = ('localhost', 8888)


def main():
    connection = json_connection.ClientConnection(SERVER_ADDR)
    request = dict(path='test/path')
    connection.send(request)
    response = connection.receive()
    print 'response = %r' % response


main()
