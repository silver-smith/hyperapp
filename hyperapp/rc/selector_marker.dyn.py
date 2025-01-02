from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    split_params,
    )


class SelectorProbe:

    def __init__(self, system_probe, ctr_collector, module_name, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
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
        result = self._fn(*args, **kw, **service_kw)
        self._add_constructor(params, result)
        return result


class SelectorGetProbe(SelectorProbe):

    def _add_constructor(self, params, result):
        pass


class SelectorPutProbe(SelectorProbe):

    def _add_constructor(self, params, result):
        pass


class SelectorDecorator:

    def __init__(self, system_probe, ctr_collector, module_name, probe_cls):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._probe_cls = probe_cls

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return self._probe_cls(self._system, self._ctr_collector, self._module_name, fn)


class SelectorMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    @property
    def get(self):
        return SelectorDecorator(self._system, self._ctr_collector, self._module_name, SelectorGetProbe)

    @property
    def put(self):
        return SelectorDecorator(self._system, self._ctr_collector, self._module_name, SelectorPutProbe)
