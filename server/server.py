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
import article
import blog


LISTEN_PORT = 8888


class Server(object):

    def __init__( self ):
        Module.init_phases()
        self.init_dir = Dir(os.path.expanduser('~/'))
        ## self.init_dir = file_view.File('/etc/DIR_COLORS')

    def resolve( self, path ):
        if path.startswith('/fs/'):
            fspath = path[3:]
            return Dir(fspath)
        if path.startswith('/file/'):
            fspath = path[5:]
            return file_view.File(fspath)
        if path.startswith('/article/'):
            return article.Article(path)
        if path.startswith('/blog_entry/'):
            return blog.BlogEntry(path)

    def get_object( self, object ):
        if object is None: return None
        iface = object.iface
        return iface.get(object)

    def process_request( self, request ):
        method = request['method']
        # server-global commands
        if method == 'init':
            return self.get_object(self.init_dir)
        if method == 'get_commands':
            return self.process_get_commands(request)
        if method == 'run_module_command':
            return self.process_run_module_command(request)
        # object commands
        path = request['path']
        object = self.resolve(path)
        iface = object.iface
        return iface.process_request(object, method, request)

    def process_get_commands( self, request ):
        commands = [cmd.as_json() for cmd in Module.get_all_modules_commands()]
        return dict(commands=commands)

    def process_run_module_command( self, request ):
        module_name = request['module_name']
        command_id = request['command_id']
        obj = Module.run_module_command(module_name, command_id)
        return self.get_object(obj)

    def run( self, connection, cln_addr ):
        print 'accepted connection from %s:%d' % cln_addr
        try:
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
