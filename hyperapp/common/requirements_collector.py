from .visitor import Visitor
from .interface import (
    tObject,
    tThisProxyObject,
    tProxyObject,
    tHandle,
    tViewHandle,
    )


class RequirementsCollector(Visitor):

    def collect( self, t, value ):
        self.collected_requirements = set()
        self.dispatch(t, value)
        return list([registry, key] for registry, key in self.collected_requirements)

    def visit_hierarchy_obj( self, t, value ):
        if t is tObject:
            self.collected_requirements.add(('object', value.objimpl_id))
            if tObject.isinstance(value, tThisProxyObject) or tObject.isinstance(value, tProxyObject):
                self.collected_requirements.add(('interface', value.iface))
        if t is tHandle and tHandle.isinstance(value, tViewHandle):
            self.collected_requirements.add(('handle', value.view_id))
