from .util import encode_path
from .htypes import tCommand
from .visitor import Visitor


class RequirementsCollector(Visitor):

    def __init__(self, packet_types, core_types, param_editor_types, iface_registry):
        Visitor.__init__(self, packet_types, core_types, iface_registry)
        self._param_editor_types = param_editor_types

    def collect(self, t, value):
        self._collected_requirements = set()
        self.visit(t, value)
        return list([registry, key] for registry, key in self._collected_requirements)

    def visit_record(self, t, value):
        if t is tCommand:
            self._collected_requirements.add(('resources', encode_path(value.resource_id)))

    def visit_hierarchy_obj(self, t, tclass, value):
        self._collected_requirements.add(('class', encode_path([value._class.hierarchy.hierarchy_id, value._class.id])))
        if t is self._core_types.object:
            self._collected_requirements.add(('object', value.objimpl_id))
            if isinstance(value, self._core_types.proxy_object):
                for iface in value.facets:
                    self._collected_requirements.add(('interface', iface))
                    self._collected_requirements.add(('resources', encode_path(['interface', iface])))
        if t is self._core_types.handle and isinstance(value, self._core_types.view_handle):
            self._collected_requirements.add(('handle', value.view_id))
        if t is self._core_types.handle and isinstance(value, self._core_types.list_handle_base):
            self._collected_requirements.add(('resources', encode_path(value.resource_id)))
        if self._param_editor_types and isinstance(value, self._param_editor_types.param_editor_resource):
            assert isinstance(value.param_editor, self._param_editor_types.param_editor_impl), repr(value.param_editor)
            self._collected_requirements.add(('param_editor', value.param_editor.impl_id))

    def _interface_list_with_bases_and_facets(self, iface):
        pass
