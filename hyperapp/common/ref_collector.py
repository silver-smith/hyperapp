from .visitor import Visitor


class RefCollector(Visitor):

    def __init__(self, error_types, packet_types, core_types, iface_registry, href_types):
        super().__init__(error_types, packet_types, core_types, iface_registry)
        self._href_types = href_types

    def collect(self, t, value):
        self._collected_refs = set()
        self.visit(t, value)
        return list(self._collected_refs)

    def visit_primitive(self, t, value):
        if t is self._href_types.ref:
            self._collected_refs.add(value)
