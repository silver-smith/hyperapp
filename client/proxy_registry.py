# registries for proxy objects and requests

import weakref
from common.util import path2str
from common.interface import Interface


class RespHandler(object):

    def __init__( self, iface, command_id ):
        assert isinstance(iface, Interface), repr(iface)
        assert isinstance(command_id, basestring), repr(command_id)
        self.iface = iface
        self.command_id = command_id

    def process_response( self, response ):
        raise NotImplementedError(self.__class__)


iface_registry = {}  # iface id -> proxy object constructor
# we want only one object per path, otherwise subscription/notification won't work:
proxy_registry = weakref.WeakValueDictionary()  # path -> ProxyObject
pending_requests = weakref.WeakValueDictionary()  # request_id -> RespHandler


def register_iface( id, obj_ctr ):
    iface_registry[id] = obj_ctr

def resolve_iface( id ):
    return iface_registry[id]


def register_proxy( path, obj ):
    path_str = path2str(path)
    assert path_str not in proxy_registry, repr(path)
    proxy_registry[path_str] = obj
    print '< registered in registry:', path, obj

def resolve_proxy( path ):
    obj = proxy_registry.get(path2str(path))
    if obj:
        print '> resolved from registry:', path, obj
    return obj

def process_updates( updates ):
    for path, diff in updates:
        obj = resolve_proxy(path)
        if obj:
            obj.process_update(diff)

def process_received_notification( notification ):
    process_updates(notification.updates)

def process_received_response( response ):
    process_received_notification(response)
    resp_handler = pending_requests.get(response.request_id)
    if not resp_handler:
        print 'Received response #%s for a missing (already closed) object, ignoring' % response.request_id
        return
    resp_handler.process_response(response)


def register_resp_handler( request_id, resp_handler ):
    assert isinstance(resp_handler, RespHandler), repr(resp_handler)
    assert request_id not in pending_requests, repr(request_id)
    pending_requests[request_id] = resp_handler
