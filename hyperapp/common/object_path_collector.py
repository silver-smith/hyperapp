from .visitor import Visitor
from .interface import (
    tObject,
    tProxyObject,
    )


class ObjectPathCollector(Visitor):

    def collect( self, t, value ):
        self.collected_paths = set()
        self.dispatch(t, value)
        return [list(path) for path in self.collected_paths]

    def visit_hierarchy_obj( self, t, value ):
        if t is tObject and tObject.isinstance(value, tProxyObject):
            self.collected_paths.add(tuple(value.path))
