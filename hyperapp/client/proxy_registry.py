# registries for proxy objects and requests

import weakref
from .objimpl_registry import objimpl_registry


# all proxy objects are registered in this class
# in particular, to avoid multiple proxy objects with the same url
# also used to distribute received updates (by Server class)
class ProxyRegistry(object):

    def __init__( self ):
        self.instances = weakref.WeakValueDictionary()   # (server id, path str) -> ProxyObject

    def register( self, server, path, object ):
        key = self._make_key(server, path)
        assert key not in self.instances, repr(key)  # Already registered. Duplicate?
        self.instances[key] = object

    def resolve( self, server_public_key, path ):
        key = self._make_key(server_public_key, path)
        return self.instances.get(key)

    def _make_key( self, server_public_key, path ):
        return (server_public_key.get_id(),) + tuple(path)


proxy_registry = ProxyRegistry()
