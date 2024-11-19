from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    split_params,
    )


class CrudDecorator:

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return fn


class CrudMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    def __getattr__(self, action):
        return CrudDecorator()
