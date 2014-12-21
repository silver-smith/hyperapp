#!/usr/bin/env python

import json_connection


LISTEN_PORT = 8888


def server_fn( connection, cln_addr ):
    print 'accepted connection from %s:%d' % cln_addr
    try:
        row_count = 0
        rpc_count = 0
        while True:
            request = connection.receive()
            print 'request: %r' % request
            method = request['method']
            if method == 'load':
                row_count = 10
                response = dict(
                    columns=[dict(id='key', title='the Key'),
                             dict(id='column-1', title='Column 1'),
                             dict(id='column-2', title='Column 2'),
                             dict(id='column-3', title='Column 3'),
                             dict(id='column-4', title='Column 4')],
                    initial_rows=[['cell#%d.%d/init' % (i, j) for j in range(5)] for i in range(row_count)])
            elif method == 'get_rows':
                rpc_count += 1
                response = dict(rows=[['cell#%d.%d/rpc-%s' % (row_count + i, j, rpc_count) for j in range(5)] for i in range(10)])
                row_count += 10
            else:
                response = None
            connection.send(response)
    except json_connection.Error as x:
        print x
            


def main():
    server = json_connection.Server(LISTEN_PORT, server_fn)
    server.run()


main()
