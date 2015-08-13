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

    def process_response( self, server, response ):
        raise NotImplementedError(self.__class__)


class ProxyRegistry(object):

    def __init__( self ):
        self.proxy_classes = {}  # proxy id -> class
        self.proxy_instances = weakref.WeakValueDictionary()   # server locator + path str -> proxy class instance
        self.pending_requests = weakref.WeakValueDictionary()  # request_id -> RespHandler

    def register_class( self, cls ):
        self.proxy_classes[cls.get_proxy_id()] = cls

    # we want only one object per server+path, otherwise subscription/notification won't work
    def register_instance( self, obj ):
        id = '%s %s' % (obj.server.get_locator(), path2str(obj.path))
        assert id not in self.proxy_classes, repr(id)
        self.proxy_instances[id] = obj
        print '< registered in registry:', id, obj

    def resolve( self, server, path, proxy_id, iface ):
        id = '%s %s' % (server.get_locator(), path2str(path))
        obj = self.proxy_instances.get(id)
        if obj:
            return obj
        cls = self.proxy_classes.get(proxy_id)
        assert cls, repr(proxy_id)  # Unknown proxy id
        obj = cls(server, path, iface)
        self.proxy_instances[id] = obj
        return obj

    def _resolve_instance( self, server, path ):
        id = '%s %s' % (server.get_locator(), path2str(path))
        return self.proxy_instances.get(id)

    def _process_updates( self, server, updates ):
        for update in updates:
            obj = self._resolve_instance(server, update.path)
            if obj:
                obj.process_update(update.diff)

    def process_received_notification( self, server, notification ):
        self._process_updates(server, notification.updates)

    def process_received_response( self, server, response ):
        self._process_updates(server, response.updates)
        resp_handler = self.pending_requests.get(response.request_id)
        if not resp_handler:
            print 'Received response #%s for a missing (already closed) object, ignoring' % response.request_id
            return
        resp_handler.process_response(server, response)

    def register_resp_handler( self, request_id, resp_handler ):
        assert isinstance(resp_handler, RespHandler), repr(resp_handler)
        assert request_id not in self.pending_requests, repr(request_id)
        self.pending_requests[request_id] = resp_handler


proxy_registry = ProxyRegistry()
