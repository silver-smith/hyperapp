import json_connection
import iface_registry


class Server(object):

    def __init__( self, addr ):
        self.connection = json_connection.ClientConnection(('localhost', 8888))
        
    def execute_request( self, request ):
        self.connection.send(request)
        return self.connection.receive()

    def get_object( self, request ):
        response = self.execute_request(request)
        iface_id = response['iface_id']
        obj_ctr = iface_registry.resolve_iface(iface_id)
        return obj_ctr(self, response)
