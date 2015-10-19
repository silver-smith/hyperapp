# registries for proxy objects and requests

import weakref
from ..common.util import path2str


class ProxyRegistry(object):

    def __init__( self ):
        self.instances = weakref.WeakValueDictionary()   # (server locator, path str) -> ProxyObject

    def register( self, server, path, object ):
        key = self._make_key(server, path)
        self.instances[key] = object

    def resolve( self, server, path ):
        key = self._make_key(server, path)
        return self.instances.get(key)

    def _make_key( self, server, path ):
        return (server.get_locator(), path2str(path))


proxy_registry = ProxyRegistry()
