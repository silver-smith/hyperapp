import weakref
from util import path2str
import json_connection
import iface_registry
import view_registry


# we want only one object per path, otherwise subscription/notification won't work
proxy_registry = weakref.WeakValueDictionary()  # path -> ProxyObject


def register_proxy( path, proxy_object ):
    path_str = path2str(path)
    assert path_str not in proxy_registry, repr(path)
    proxy_registry[path_str] = proxy_object

def resolve_proxy( path ):
    print 'resolve_proxy:', path2str(path), proxy_registry.get(path2str(path))
    return proxy_registry.get(path2str(path))


def resolve_object( server, resp ):
    iface_id = resp['iface_id']
    path = resp['path']
    object = resolve_proxy(path)
    if not object:
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
        return Response(self, self.connection.receive())

    def request_an_object( self, request ):
        response = self.execute_request(request)
        return response.object()
