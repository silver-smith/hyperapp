import json_connection


class Server(object):

    def __init__( self, addr ):
        self.connection = json_connection.ClientConnection(('localhost', 8888))
        
    def execute_request( self, request ):
        self.connection.send(request)
        return self.connection.receive()
