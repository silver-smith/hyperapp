from hyperapp.boot.htypes import TRecord

from .services import (
    deduce_t,
    )
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    split_params,
    )
from .code.selector_ctr import SelectorGetTemplateCtr, SelectorPickTemplateCtr


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
        if list(params.ctx_names) != ['value']:
            raise RuntimeError(f"{self._fn}: Expected single non-service parameter, 'value': {params.ctx_names}")
        value = params.values['value']
        value_t = deduce_t(value)
        model_t = deduce_t(result)
        assert isinstance(model_t, TRecord), model_t
        ctr = SelectorGetTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_params=params.service_names,
            value_t=value_t,
            model_t=model_t,
            )
        self._ctr_collector.add_constructor(ctr)


class SelectorPickProbe(SelectorProbe):

    def _add_constructor(self, params, result):
        value_t = deduce_t(result)
        ctr = SelectorPickTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            ctx_params=params.ctx_names,
            service_params=params.service_names,
            value_t=value_t,
            )
        self._ctr_collector.add_constructor(ctr)


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
    def pick(self):
        return SelectorDecorator(self._system, self._ctr_collector, self._module_name, SelectorPickProbe)
