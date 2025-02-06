from .services import (
    deduce_t,
    )
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    split_params,
    )
from .code.editor_ctr import EditorDefaultTemplateCtr


class EditorDefaultProbe:

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

    def _add_constructor(self, params, result):
        result_t = deduce_t(result)
        ctr = EditorDefaultTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            ctx_params=params.ctx_names,
            service_params=params.service_names,
            value_t=result_t,
            )
        self._ctr_collector.add_constructor(ctr)


class EditorDefaultDecorator:

    def __init__(self, system_probe, ctr_collector, module_name):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return EditorDefaultProbe(self._system, self._ctr_collector, self._module_name, fn)


class EditorMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    @property
    def default(self):
        return EditorDefaultDecorator(self._system, self._ctr_collector, self._module_name)
