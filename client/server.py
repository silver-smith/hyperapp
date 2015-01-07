import json_connection
import iface_registry
import view_registry


class Server(object):

    def __init__( self, addr ):
        self.connection = json_connection.ClientConnection(('localhost', 8888))
        
    def execute_request( self, request ):
        self.connection.send(request)
        return self.connection.receive()

    def resp2object( self, response ):
        iface_id = response['iface_id']
        obj_ctr = iface_registry.resolve_iface(iface_id)
        return obj_ctr(self, response)

    def get_object( self, request ):
        response = self.execute_request(request)
        return self.resp2object(response)

    def get_view( self, request ):
        response = self.execute_request(request)
        object = self.resp2object(response)
        view_id = response['view_id']
        handle_ctr = view_registry.resolve_view(view_id)
        return handle_ctr(object)

