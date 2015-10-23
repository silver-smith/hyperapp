# registries for proxy objects and requests

import weakref
from ..common.util import encode_url
from .objimpl_registry import objimpl_registry


class ProxyClassRegistry(object):

    def __init__( self ):
        self.implid2class = {}  # objimpl_id -> proxy class

    def register( self, cls ):
        objimpl_id = cls.get_objimpl_id()
        assert objimpl_id not in self.implid2class, repr(objimpl_id)  # Already registered. Duplicate?
        objimpl_registry.register(objimpl_id, cls.produce_obj_by_objinfo)
        self.implid2class[objimpl_id] = cls

    def resolve( self, objimpl_id ):
        assert objimpl_id in self.implid2class, repr(objimpl_id)  # Not found
        return self.implid2class[objimpl_id]


class ProxyRegistry(object):

    def __init__( self ):
        self.instances = weakref.WeakValueDictionary()   # (server locator, path str) -> ProxyObject

    def register( self, server, path, object ):
        key = self._make_key(server, path)
        assert key not in self.instances, repr(key)  # Already registered. Duplicate?
        self.instances[key] = object

    def resolve( self, server, path ):
        key = self._make_key(server, path)
        return self.instances.get(key)

    def _make_key( self, server, path ):
        return encode_url(server.make_url(path))


proxy_class_registry = ProxyClassRegistry()
proxy_registry = ProxyRegistry()
