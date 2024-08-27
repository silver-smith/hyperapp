import enum
import inspect
from collections import namedtuple

from hyperapp.common.htypes import Type


class MarkMode(enum.Enum):
    import_ = enum.auto()
    test = enum.auto()


class NoOpMarker:

    def __getattr__(self, name):
        return NoOpMarker()

    def __call__(self, *args, **kw):
        if not kw and len(args) == 1:
            if not isinstance(args[0], (Type, str)):
                return args[0]
        return NoOpMarker()


class MarkerCtl:

    _ModuleRec = namedtuple('_ModuleRec', 'module_name mode')

    def __init__(self):
        self._markers = {}  # Marker by name.
        self._pyname_to_hname = {}  # Wanted modules.

    def add_wanted_module(self, pyname, hname, mode):
        self._pyname_to_hname[pyname] = self._ModuleRec(hname, mode)

    def clear_wanted_modules(self):
        self._pyname_to_hname.clear()

    def set_marker(self, name, marker):
        self._markers[name] = marker

    def clear_markers(self):
        self._markers.clear()

    def get(self, python_module_name, marker_name):
        try:
            rec = self._pyname_to_hname[python_module_name]
        except KeyError:
            return NoOpMarker()
        marker = self._markers[marker_name]
        return marker.resolve(rec.module_name, rec.mode)


class Markers:

    def __init__(self, ctl):
        self._ctl = ctl

    def __getattr__(self, name):
        frame = inspect.stack()[1].frame
        python_module_name = frame.f_globals['__name__']
        return self._ctl.get(python_module_name, name)


_marker_ctl = MarkerCtl()
mark = Markers(_marker_ctl)


def marker_ctl():
    return _marker_ctl
