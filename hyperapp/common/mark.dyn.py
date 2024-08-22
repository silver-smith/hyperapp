from hyperapp.common.htypes import Type


class NoOpMarker:

    def __getattr__(self, name):
        return NoOpMarker()

    def __call__(self, *args, **kw):
        if not kw and len(args) == 1:
            if not isinstance(args[0], Type):
                return args[0]
        return NoOpMarker()


class MarkerCtl:

    def __init__(self):
        self._markers = {}

    def set(self, name, marker):
        self._markers[name] = marker

    def clear(self):
        self._markers.clear()

    def get(self, name):
        if self._markers:
            return self._markers[name]
        else:
            return NoOpMarker()


class Markers:

    def __init__(self, ctl):
        self._ctl = ctl

    def __getattr__(self, name):
        return self._ctl.get(name)


_marker_ctl = MarkerCtl()
mark = Markers(_marker_ctl)


def marker_ctl():
    return _marker_ctl
