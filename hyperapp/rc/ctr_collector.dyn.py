from collections import namedtuple


class CtrCollector:

    NotSet = object()
    Ignore = object()
    Set = namedtuple('Set', 'module_name')

    def __init__(self, config):
        self._pyname_to_hname = {
            module.__name__: self.Set(name)
            for name, module in config.items()
            }
        self._constructors = []

    def ignore_module(self, python_module_name):
        self._pyname_to_hname[python_module_name] = self.Ignore

    def get_module_name(self, python_module_name):
        try:
            return self._pyname_to_hname[python_module_name]
        except KeyError:
            return self.NotSet

    def add_constructor(self, ctr):
        self._constructors.append(ctr)

    @property
    def constructors(self):
        return self._constructors


def ctr_collector(config):
    return CtrCollector(config)
