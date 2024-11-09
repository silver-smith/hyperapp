from functools import partial

from .services import pyobj_creg


class MarkerTemplate:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            name=piece.name,
            fn=pyobj_creg.invite(piece.function),
            service_params=piece.service_params,
            )

    def __init__(self, name, fn, service_params):
        self.name = name
        self._fn = fn
        self._service_params = service_params

    @property
    def key(self):
        return self.name

    def __repr__(self):
        return f"<MarkerTemplate {self.name}: {self._fn} {self._service_params}>"

    def resolve(self, system, service_name):
        kw = {
            name: system.resolve_service(name)
            for name in self._service_params
            }
        return Marker(self._fn, kw)


class Marker:

    def __init__(self, fn, service_kw):
        self._fn = fn
        self._service_kw = service_kw

    def resolve(self, module_name):
        kw = {
            **self._service_kw,
            'module_name': module_name,
            }
        if type(self._fn) is type:
            # A class.
            return self._fn(**kw)
        else:
            # A function.
            return partial(self._fn, **kw)


def marker_registry(config, ctr_collector, marker_ctl):
    for name, marker in config.items():
        marker_ctl.set_marker(name, marker)
    yield
    marker_ctl.clear_markers()
