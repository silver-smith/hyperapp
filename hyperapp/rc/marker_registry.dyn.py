from functools import partial

from .services import pyobj_creg


def resolve_marker_cfg_value(piece, key, system, service_name):
    fn = pyobj_creg.invite(piece.function)
    kw = {
        name: system.resolve_service(name)
        for name in piece.service_params
        }
    return Marker(fn, kw)


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
