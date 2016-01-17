# server response data manipulation:
#  create proxy objects using contents, replace tThisProxyObject (without endpoint) with tProxyObject (with endpoint)

from ..common.interface import TOptional, tHandle, tObject, tThisProxyObject, tProxyObject, iface_registry
from ..common.mapper import Mapper
from ..common.visual_rep import pprint
from .proxy_registry import ProxyRegistry, proxy_class_registry


class ProxyObjectMapper(Mapper):

    @classmethod
    def map( cls, value, proxy_registry, server ):
        mapper = cls(proxy_registry, server)
        return Mapper.map(mapper, TOptional(tHandle), value)

    def __init__( self, proxy_registry, server ):
        assert isinstance(proxy_registry, ProxyRegistry), repr(proxy_registry)
        Mapper.__init__(self)
        self.proxy_registry = proxy_registry
        self.server = server

    def map_hierarchy_obj( self, tclass, value ):
        if tclass.issubclass(tThisProxyObject):
            print '======== received proxy object ========'
            pprint(tObject, value)
            print '======================================='
            obj = self.proxy_registry.resolve(self.server, value.path)
            if obj is None:
                iface = iface_registry.resolve(value.iface)
                cls = proxy_class_registry.resolve(value.objimpl_id)
                obj = cls.produce_obj(self.server, value.path, iface)
                self.proxy_registry.register(self.server, value.path, obj)
            obj.set_contents(value.contents)
        return value
