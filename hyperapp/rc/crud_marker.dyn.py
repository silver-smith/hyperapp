from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    split_params,
    )


class CrudProbe:

    def __init__(self, system_probe, ctr_collector, module_name, action, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._action = action
        self._fn = fn
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

    def __call__(self, *args, **kw):
        params = split_params(self._fn, args, kw)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in params.service_names
            }
        return self._fn(*args, **kw, **service_kw)


class CrudDecorator:

    def __init__(self, system_probe, ctr_collector, module_name, action):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._action = action

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return CrudProbe(self._system, self._ctr_collector, self._module_name, self._action, fn)


class CrudMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    def __getattr__(self, action):
        return CrudDecorator(self._system, self._ctr_collector, self._module_name, action)
