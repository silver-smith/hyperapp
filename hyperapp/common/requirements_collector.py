from .util import encode_path
from .htypes import (
    tCommand,
    tObject,
    tProxyObject,
    tHandle,
    tViewHandle,
    )
from .visitor import Visitor


class RequirementsCollector(Visitor):

    def collect( self, t, value ):
        self._collected_requirements = set()
        self.visit(t, value)
        return list([registry, key] for registry, key in self._collected_requirements)

    def visit_record( self, t, value ):
        if t is tCommand:
            self._collected_requirements.add(('resources', encode_path(value.resource_id)))

    def visit_hierarchy_obj( self, t, tclass, value ):
        if t is tObject:
            self._collected_requirements.add(('object', value.objimpl_id))
            if isinstance(value, tProxyObject):
                for iface in value.facets:
                    self._collected_requirements.add(('interface', iface))
        if t is tHandle and isinstance(value, tViewHandle):
            self._collected_requirements.add(('handle', value.view_id))
