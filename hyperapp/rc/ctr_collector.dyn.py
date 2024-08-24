from collections import namedtuple

from hyperapp.resource.python_module import make_module_name

from .services import mosaic


class CtrCollector:

    NotSet = object()
    Ignore = object()
    Set = namedtuple('Set', 'module_name')

    def __init__(self, config, marker_ctl):
        self._marker_ctl = marker_ctl
        self._pyname_to_action = {
            module.__name__: self.Set(name)
            for name, module in config.items()
            }
        self._constructors = []

    def ignore_module(self, python_module_name):
        self._pyname_to_action[python_module_name] = self.Ignore

    def set_wanted_piece(self, module_name, module_piece):
        python_module_name = make_module_name(mosaic, module_piece)
        self._pyname_to_action[python_module_name] = self.Set(module_name)

    def get_module_action(self, python_module_name):
        try:
            return self._pyname_to_action[python_module_name]
        except KeyError:
            return self.NotSet

    def init_markers(self):
        for pyname, action in self._pyname_to_action.items():
            if type(action) is self.Set:
                self._marker_ctl.add_wanted_module(pyname, action.module_name)

    def add_constructor(self, ctr):
        self._constructors.append(ctr)

    @property
    def constructors(self):
        return self._constructors


def ctr_collector(config, marker_ctl):
    collector =  CtrCollector(config, marker_ctl)
    yield collector
    marker_ctl.clear_wanted_modules()
