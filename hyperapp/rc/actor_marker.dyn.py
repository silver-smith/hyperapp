from hyperapp.common.htypes import Type

from .services import deduce_t
from .code.actor_ctr import ActorProbeCtr, ActorTemplateCtr
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    is_cls_arg,
    fn_params,
    )


class ServiceActorProbe:

    def __init__(self, system_probe, ctr_collector, module_name, service_name, fn, t=None):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name
        self._fn = fn
        self._t = t
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

    def __call__(self, *args, **kw):
        params = fn_params(self._fn)
        piece_param_ofs = 0
        if args and is_cls_arg(self._fn, args[0]):
            # self._fn is a classmethod and args[0] is a 'cls' argument.
            piece_param_ofs = 1
        if len(args) < piece_param_ofs + 1:
            raise RuntimeError(f"First parameter expected is a piece: {self._fn!r}")
        piece = args[piece_param_ofs]
        creg_param_count = len(args) - piece_param_ofs - 1 + len(kw)
        creg_params = params[piece_param_ofs + 1:creg_param_count + piece_param_ofs + 1]
        service_params = params[creg_param_count + piece_param_ofs + 1:]
        if self._t is None:
            t = deduce_t(piece)
        else:
            t = self._t
        self._add_constructor(t, creg_params, service_params)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in service_params
            }
        return self._fn(*args, **kw, **service_kw)

    def _add_constructor(self, t, creg_params, service_params):
        ctr = ActorTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_name=self._service_name,
            t=t,
            creg_params=creg_params,
            service_params=service_params,
            )
        self._ctr_collector.add_constructor(ctr)


class ServiceActorDecorator:

    def __init__(self, system, ctr_collector, module_name, service_name, t):
        self._system = system
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name
        self._t = t

    def __call__(self, fn):
        qual_name = fn.__qualname__.split('.')
        check_not_classmethod(fn)
        check_is_function(fn)
        params = fn_params(fn)
        ctr = ActorProbeCtr(
            attr_qual_name=qual_name,
            service_name=self._service_name,
            t=self._t,
            params=params,
            )
        self._ctr_collector.add_constructor(ctr)
        return ServiceActorProbe(self._system, self._ctr_collector, self._module_name, self._service_name, fn, self._t)


class ServiceActorMarker:

    def __init__(self, system_probe, ctr_collector, module_name, service_name):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name

    def __call__(self, fn_or_t):
        if isinstance(fn_or_t, Type):
            # Type-specialized variant (@mark.actor.my_registry(my_type)).
            return ServiceActorDecorator(self._system, self._ctr_collector, self._module_name, self._service_name, fn_or_t)
        check_not_classmethod(fn_or_t)
        check_is_function(fn_or_t)
        # Not type-specialized variant  (@mark.actor.my_registry).
        return ServiceActorProbe(self._system, self._ctr_collector, self._module_name, self._service_name, fn_or_t)


class ActorMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    def __getattr__(self, service_name):
        return ServiceActorMarker(self._system, self._ctr_collector, self._module_name, service_name)
