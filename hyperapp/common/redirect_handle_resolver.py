from .interface import tRedirectHandle
from .visitor import Visitor
from .mapper import Mapper


class RedirectHandleCollector(Visitor):

    @classmethod
    def collect( cls, t, value ):
        collector = cls()
        collector.visit(t, value)
        return collector.redirect_handles

    def __init__( self ):
        self.redirect_handles = []

    def visit_hierarchy_obj( self, t, tclass, value ):
        if tclass is tRedirectHandle:
            self.redirect_handles.append(value)
