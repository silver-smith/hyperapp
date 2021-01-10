from .visitor import Visitor


class ObjectPathCollector(Visitor):

    def collect(self, t, value):
        self.collected_paths = set()
        self.visit(t, value)
        return [list(path) for path in self.collected_paths]
