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
        if response is None: return None
        iface_id = response['iface_id']
        obj_ctr = iface_registry.resolve_iface(iface_id)
        return obj_ctr(self, response)

    def resp2handle( self, response ):
        object = self.resp2object(response)
        if object is None: return None
        view_id = response['view_id']
        handle_ctr = view_registry.resolve_view(view_id)
        return handle_ctr(object)

    def get_object( self, request ):
        response = self.execute_request(request)
        return self.resp2object(response)

    def get_handle( self, request ):
        response = self.execute_request(request)
        assert response['action'] == 'open'
        return self.resp2handle(response['obj'])
