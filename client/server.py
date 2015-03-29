from PySide import QtNetwork
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

    addr2socket = {}

    def __init__( self, addr ):
        self.addr = addr
        self._open_connection()

    def __getstate__( self ):
        return dict(addr=self.addr)

    def __setstate__( self, state ):
        self.addr = state['addr']
        self._open_connection()

    def _open_connection( self ):
        self.socket = self.addr2socket.get(self.addr)
        if not self.socket:
            host, port = self.addr
            print 'Network: connecting to %s:%d' % (host, port)
            self.socket = QtNetwork.QTcpSocket()
            self.socket.error.connect(self._on_error)
            self.socket.stateChanged.connect(self._on_state_changed)
            self.socket.hostFound.connect(self._on_host_found)
            self.socket.connected.connect(self._on_connected)
            self.socket.connectToHost(host, port)
            self.addr2socket[self.addr] = self.socket

    def _trace( self, msg ):
        host, port = self.addr
        print 'Network, connection to %s:%d: %s' % (host, port, msg)

    def _on_error( self, msg ):
        self._trace('Error: %s' % msg)

    def _on_state_changed( self, state ):
        self._trace('State changed: %r' % state)

    def _on_host_found( self ):
        self._trace('Host found')

    def _on_connected( self ):
        self._trace('Connected')

    def execute_request( self, request ):
        return
        self.connection.send(request)
        response = Response(self, self.connection.receive())
        ProxyObject.process_updates(response.get_updates())
        return response

    def request_an_object( self, request ):
        return
        response = self.execute_request(request)
        return response.object()

    def __del__( self ):
        print '~Server', self.addr
