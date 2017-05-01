from .visitor import Visitor


class ObjectPathCollector(Visitor):

    def __init__(self, core_types):
        self._core_types = core_types

    def collect(self, t, value):
        self.collected_paths = set()
        self.visit(t, value)
        return [list(path) for path in self.collected_paths]

    def visit_hierarchy_obj(self, t, tclass, value):
        if t is self._core_types.object and isinstance(value, self._core_types.proxy_object):
            self.collected_paths.add(tuple(value.path))
