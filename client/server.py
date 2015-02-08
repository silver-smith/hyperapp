import json_connection
import iface_registry
import view_registry


def resolve_object( server, resp ):
    iface_id = resp['iface_id']
    obj_ctr = iface_registry.resolve_iface(iface_id)
    object = obj_ctr(server, resp)
    view_id = resp['view_id']
    handle_ctr = view_registry.resolve_view(view_id)
    return handle_ctr(object)


class DictObject(object):

    def __init__( self, d ):
        self._d = d

    def __getattr__( self, attr ):
        return self._d[attr]


class Response(object):

    def __init__( self, server, resp_dict ):
        self.server = server
        self.resp_dict = resp_dict

    @property
    def result( self ):
        if 'result' in self.resp_dict:
            return DictObject(self.resp_dict['result'])

    def object( self ):
        if 'object' in self.resp_dict:
            return resolve_object(self.server, self.resp_dict['object'])


class Server(object):

    def __init__( self, addr ):
        self.connection = json_connection.ClientConnection(('localhost', 8888))
        
    def execute_request( self, request ):
        self.connection.send(request)
        return Response(self, self.connection.receive())
