from ..common.interface import TOptional, tHandle, tRedirectHandle
from ..common.visitor import Visitor
from ..common.mapper import Mapper


class RedirectHandleCollector(Visitor):

    @classmethod
    def collect( cls, value ):
        collector = cls()
        collector.visit(TOptional(tHandle), value)
        return collector.redirect_handles

    def __init__( self ):
        self.redirect_handles = []

    def visit_hierarchy_obj( self, t, tclass, value ):
        if tclass is tRedirectHandle:
            self.redirect_handles.append(value)


class RedirectHandleMapper(Mapper):

    @classmethod
    def map( cls, value, map_to_handles ):
        mapper = cls(map_to_handles)
        return Mapper.map(mapper, TOptional(tHandle), value)

    def __init__( self, map_to_handles ):
        assert isinstance(map_to_handles, list) and len(map_to_handles) >= 1, repr(map_to_handles)
        Mapper.__init__(self)
        self.map_to_handles = map_to_handles[:]

    def map_hierarchy_obj( self, tclass, value ):
        if tclass is tRedirectHandle:
            assert self.map_to_handles  # there are more redirect handles than handles to map are provided
            value = self.map_to_handles[0]
            del self.map_to_handles[0]
        return value
