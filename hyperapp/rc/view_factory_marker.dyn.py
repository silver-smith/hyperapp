from enum import Enum

from hyperapp.boot.htypes import Type
from hyperapp.boot.htypes.deduce_value_type import DeduceTypeError

from .services import (
    deduce_t,
    )
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    process_awaitable_result,
    split_params,
    )
from .code.probe import ProbeBase
from .code.view_factory_ctr import ViewFactoryTemplateCtr


class ViewFactoryProbe(ProbeBase):

    class Kind(Enum):
        view = 'view'
        model_t = 'model_t'
        ui_t = 'ui_t'

    def __init__(self, system_probe, ctr_collector, module_name, fn, kind, model_t=None):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._fn = fn
        self._kind = kind
        self._model_t = model_t
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

    def __call__(self, *args, **kw):
        params = split_params(self.real_fn, args, kw)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in params.service_names
            }
        model_t = None
        ui_t_t = None
        if self._kind == self.Kind.view:
            pass
        elif self._kind == self.Kind.model_t:
            model_t = self._model_t
        elif self._kind == self.Kind.ui_t:
            ui_t_t = self._deduce_ui_t_t(params)
        else:
            assert False, self._kind
        result = self._fn(*args, **kw, **service_kw)
        return process_awaitable_result(self._add_constructor, result, params, model_t, ui_t_t)

    def _deduce_ui_t_t(self, params):
        if len(params.ctx_names) < 1 or params.ctx_names[0] != 'piece':
            raise RuntimeError(
                "First parameter for ui_t view factory expected to be a 'piece':"
                f" {self.real_fn!r}: {params.ctx_names!r}")
        if 'system_fn' not in params.ctx_names:
            raise RuntimeError(
                "'system_fn' parameter is expected for ui_t view factory:"
                f" {self.real_fn!r}: {params.ctx_names!r}")
        return deduce_t(params.values['piece'])

    def _add_constructor(self, result, params, model_t, ui_t_t):
        try:
            result_t = deduce_t(result)
        except DeduceTypeError as x:
            raise RuntimeError(f"{self.real_fn}: Returned not a deducible data type: {result!r}") from x
        ctr = ViewFactoryTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=params.real_qual_name(self.real_fn),
            model_t=model_t,
            ui_t_t=ui_t_t,
            ctx_params=params.ctx_names,
            service_params=params.service_names,
            view_t=result_t,
            )
        self._ctr_collector.add_constructor(ctr)


class Marker:

    def __init__(self, module_name, system, ctr_collector, kind, model_t=None):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector
        self._kind = kind
        self._model_t = model_t


class FnMarker(Marker):

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return ViewFactoryProbe(
            self._system, self._ctr_collector, self._module_name, fn, self._kind, self._model_t)


class TypeMarker(Marker):

    def __call__(self, model_t):
        if not isinstance(model_t, Type):
            raise RuntimeError(f"Model view factory should have type specialization: {model_t!r}")
        return FnMarker(
            self._module_name, self._system, self._ctr_collector, self._kind, model_t)


class ViewFactoryMarker(FnMarker):

    def __init__(self, module_name, system, ctr_collector):
        super().__init__(module_name, system, ctr_collector, kind=ViewFactoryProbe.Kind.view)

    @property
    def model_t(self):
        return TypeMarker(self._module_name, self._system, self._ctr_collector, kind=ViewFactoryProbe.Kind.model_t)

    @property
    def ui_t(self):
        return FnMarker(self._module_name, self._system, self._ctr_collector, kind=ViewFactoryProbe.Kind.ui_t)
