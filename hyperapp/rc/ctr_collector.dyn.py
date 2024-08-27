from collections import namedtuple

from hyperapp.resource.python_module import make_module_name

from .services import mosaic
from .code.mark import MarkMode


class CtrCollector:

    class Action:
        NotSet = object()
        Ignore = object()
        Set = namedtuple('Set', 'module_name mode')

    def __init__(self, config, marker_ctl):
        self._marker_ctl = marker_ctl
        self._pyname_to_action = {
            module.__name__: self.Action.Set(name, mode)
            for name, (module, mode) in config.items()
            }
        self._constructors = []

    def ignore_module(self, module_piece):
        python_module_name = make_module_name(mosaic, module_piece)
        self._pyname_to_action[python_module_name] = self.Action.Ignore

    def set_wanted_import(self, module_name, module_piece):
        python_module_name = make_module_name(mosaic, module_piece)
        self._pyname_to_action[python_module_name] = self.Action.Set(module_name, mode=MarkMode.import_)

    def get_module_action(self, python_module_name):
        try:
            return self._pyname_to_action[python_module_name]
        except KeyError:
            return self.Action.NotSet

    def init_markers(self):
        for pyname, action in self._pyname_to_action.items():
            if type(action) is self.Action.Set:
                self._marker_ctl.add_wanted_module(pyname, action.module_name, action.mode)

    def add_constructor(self, ctr):
        self._constructors.append(ctr)

    @property
    def constructors(self):
        return self._constructors


def ctr_collector(config, marker_ctl):
    collector =  CtrCollector(config, marker_ctl)
    yield collector
    marker_ctl.clear_wanted_modules()
