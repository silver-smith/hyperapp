#!/usr/bin/env python

import traceback
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
                    columns=[dict(id='key', title=None),
                             dict(id='column-0', title='Column 0'),
                             dict(id='column-1', title='Column 1'),
                             dict(id='column-2', title='Column 2'),
                             dict(id='column-3', title='Column 3'),
                             dict(id='column-4', title='Column 4')],
                    rows=[[i] + ['cell#%d.%d/init' % (i, j) for j in range(5)] for i in range(row_count)])
            elif method == 'get_rows':
                count = max(request['count'], 10)
                key = request['key']
                rpc_count += 1
                response = dict(rows=[[key + 1 + i] + ['cell#%d.%d/rpc-%s' % (key + 1 + i, j, rpc_count) for j in range(5)] for i in range(count)])
                row_count += 10
            else:
                response = None
            connection.send(response)
    except json_connection.Error as x:
        print x
    except:
        traceback.print_exc()
            


def main():
    server = json_connection.Server(LISTEN_PORT, server_fn)
    server.run()


main()
