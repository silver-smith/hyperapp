#!/usr/bin/env python

import sys
import os
import os.path
import traceback
import json_connection
from fs import Dir

LISTEN_PORT = 8888


class Server(object):

    init_dir = Dir(os.path.expanduser('~/'))

    def resolve( self, path ):
        assert path.startswith('/fs/')
        fspath = path[3:]
        return Dir(fspath)

    def resp_elements( self, dir, count=None, key=None ):
        return [elt.as_json() for elt in dir.get_elements(count, key)]

    def resp_object( self, dir ):
        return dict(
            path=dir.path,
            dir_commands=[cmd.as_json() for cmd in dir.dir_commands()],
            columns=[column.as_json() for column in dir.columns],
            elements=self.resp_elements(dir))

    def process_request( self, request ):
        method = request['method']
        if method == 'init':
            return self.resp_object(self.init_dir)
        path = request['path']
        dir = self.resolve(path)
        if method == 'get_elements':
            key = request['key']
            count = request['count']
            return dict(elements=self.resp_elements(dir, count, key))
        elif method == 'element_command':
            command_id = request['command_id']
            element_key = request['element_key']
            new_dir = dir.run_element_command(command_id, element_key)
            return self.resp_object(new_dir)
        elif method == 'dir_command':
            command_id = request['command_id']
            new_dir = dir.run_dir_command(command_id)
            return self.resp_object(new_dir)
        else:
            assert False, repr(method)

    def run( self, connection, cln_addr ):
        print 'accepted connection from %s:%d' % cln_addr
        try:
            row_count = 0
            rpc_count = 0
            while True:
                request = connection.receive()
                print 'request: %r' % request
                response = self.process_request(request)
                connection.send(response)
        except json_connection.Error as x:
            print x
        except:
            traceback.print_exc()
            


def main():
    server = json_connection.Server(LISTEN_PORT, Server().run)
    server.run()


main()
