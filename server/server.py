#!/usr/bin/env python

import sys
import os
import os.path
import traceback

sys.path.append('..')

import json_connection
from module import Module
import ponyorm_module
from fs import Dir
import file_view


LISTEN_PORT = 8888


class Server(object):

    def __init__( self ):
        Module.run_phase2_init()
        self.init_dir = Dir(os.path.expanduser('~/'))
        ## self.init_dir = file_view.File('/etc/DIR_COLORS')

    def resolve( self, path ):
        if path.startswith('/fs/'):
            fspath = path[3:]
            return Dir(fspath)
        if path.startswith('/file/'):
            fspath = path[5:]
            return file_view.File(fspath)

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
        if method == 'get_commands':
            return self.process_get_commands(request)
        if method == 'run_module_command':
            return self.process_run_module_command(request)
        path = request['path']
        dir = self.resolve(path)
        if method == 'get_elements':
            key = request['key']
            count = request['count']
            return dict(elements=self.resp_elements(dir, count, key))
        elif method == 'run_element_command':
            command_id = request['command_id']
            element_key = request['element_key']
            new_dir = dir.run_element_command(command_id, element_key)
            return self.resp_object(new_dir)
        elif method == 'run_dir_command':
            command_id = request['command_id']
            new_dir = dir.run_dir_command(command_id)
            return self.resp_object(new_dir)
        else:
            assert False, repr(method)

    def process_get_commands( self, request ):
        commands = [cmd.as_json() for cmd in Module.get_all_modules_commands()]
        return dict(commands=commands)

    def process_run_module_command( self, request ):
        module_name = request['module_name']
        command_id = request['command_id']
        obj = Module.run_module_command(module_name, command_id)
        return self.resp_object(obj)

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
    server = Server()
    json_server = json_connection.Server(LISTEN_PORT, server.run)
    json_server.run()


main()
