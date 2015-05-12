#!/usr/bin/env python

import sys
import os
import os.path
import traceback
import re
import pprint

sys.path.append('..')

import json_connection
from object import Response, Request
from module import Module
import ponyorm_module
import fs
import file_view
import article
import blog
import server_management


LISTEN_PORT = 8888


class Server(object):

    def __init__( self ):
        Module.init_phases()

    def resolve( self, path ):
        return Module.run_resolve(path)

    def process_request_raw( self, request ):
        response = self.process_request(request)
        if response is None and request.is_response_needed():
            response = request.make_response()  # client need a response to cleanup waiting response handler
        if response is not None:
            assert isinstance(response, Response), repr(response)
            return response.as_json()

    def process_request( self, request ):
        method = request['method']
        path = request['path']
        object = self.resolve(path)
        print 'Object:', object
        assert object, repr(path)  # 404: Path not found
        return object.process_request(request)

    def run( self, connection, cln_addr ):
        print 'accepted connection from %s:%d' % cln_addr
        try:
            while True:
                request = connection.receive()
                print 'request:' if 'request_id' in request else 'notification:'
                pprint.pprint(request)
                try:
                    response = self.process_request_raw(Request(request))
                except:
                    traceback.print_exc()
                    response = dict(error='Internal server error')
                if response is not None:
                    print 'response:'
                    pprint.pprint(response)
                    connection.send(response)
                else:
                    print 'no response for notification'
        except json_connection.Error as x:
            print x
        except:
            traceback.print_exc()
            


def main():
    server = Server()
    json_server = json_connection.Server(LISTEN_PORT, server.run)
    json_server.run()


main()
