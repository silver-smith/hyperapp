import json_connection
import iface_registry
import view_registry
from proxy_object import ProxyObject, ProxyListObject


def resolve_object( server, resp ):
    iface_id = resp['iface_id']
    path = resp['path']
    obj_ctr = iface_registry.resolve_iface(iface_id)
    object = obj_ctr(server, resp)
    view_id = resp['view_id']
    handle_ctr = view_registry.resolve_view(view_id)
    return handle_ctr(object, resp)


class ListDiff(object):

    @classmethod
    def from_resp( cls, d ):
        return cls(
            start_key=d['start_key'],
            end_key=d['end_key'],
            elements=[ProxyListObject.element_from_json(elt) for elt in d['elements']],
            )

    def __init__( self, start_key, end_key, elements ):
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (but not including) this one
        self.elements = elements    # with these elemenents


class ResultDict(object):

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
            return ResultDict(self.resp_dict['result'])

    def object( self ):
        if 'object' in self.resp_dict:
            return resolve_object(self.server, self.resp_dict['object'])

    def get_updates( self ):
        if 'updates' not in self.resp_dict:
            return []
        return [(path, ListDiff.from_resp(diff)) for path, diff in self.resp_dict['updates']]


class Server(object):

    addr2connection = {}

    def __init__( self, addr ):
        self.addr = addr
        self._open_connection()

    def __getstate__( self ):
        return dict(addr=self.addr)

    def __setstate__( self, state ):
        self.addr = state['addr']
        self._open_connection()

    def _open_connection( self ):
        self.connection = self.addr2connection.get(self.addr)
        if not self.connection:
            self.connection = json_connection.ClientConnection(self.addr)
            self.addr2connection[self.addr] = self.connection

    def execute_request( self, request ):
        self.connection.send(request)
        response = Response(self, self.connection.receive())
        ProxyObject.process_updates(response.get_updates())
        return response

    def request_an_object( self, request ):
        response = self.execute_request(request)
        return response.object()
