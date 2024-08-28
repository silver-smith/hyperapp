import inspect

from hyperapp.common.htypes import Type

from .services import deduce_t
from .code.actor_ctr import ActorProbeCtr, ActorTemplateCtr


def _fn_params(fn):
    if type(fn) in {classmethod, staticmethod}:
        actual_fn = inspect.unwrap(fn)
    else:
        if not inspect.isfunction(fn):
            raise RuntimeError(
                f"Unknown object attempted to be marked as an actor: {fn!r};"
                " Expected function, classmethod or staticmethod"
                )
        actual_fn = fn
    params = list(inspect.signature(actual_fn).parameters)
    if type(fn) is classmethod:
        # Remove 'cls' parameter.
        return params[1:]
    else:
        return params


class ServiceActorWrapper:

    def __init__(self, ctr_collector, module_name, service_name, t):
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name
        self._t = t

    def __call__(self, fn):
        qual_name = fn.__qualname__.split('.')
        params = _fn_params(fn)
        ctr = ActorProbeCtr(
            attr_qual_name=qual_name,
            service_name=self._service_name,
            t=self._t,
            params=params,
            )
        self._ctr_collector.add_constructor(ctr)
        return fn


class ServiceActorProbe:

    def __init__(self, system_probe, ctr_collector, module_name, service_name, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name
        self._fn = fn

    def __call__(self, *args, **kw):
        params = list(inspect.signature(self._fn).parameters)
        piece_param_ofs = 0
        if args and self._is_cls_arg(args[0]):
            # self._fn is a classmethod and args[0] is a 'cls' argument.
            piece_param_ofs = 1
        if len(args) < piece_param_ofs + 1:
            raise RuntimeError(f"First parameter expected is a piece: {self._fn!r}")
        piece = args[piece_param_ofs]
        creg_param_count = len(args) - piece_param_ofs - 1 + len(kw)
        creg_params = params[piece_param_ofs + 1:creg_param_count + piece_param_ofs + 1]
        service_params = params[creg_param_count + piece_param_ofs + 1:]
        t = deduce_t(piece)
        self._add_constructor(t, creg_params, service_params)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in service_params
            }
        return self._fn(*args, **kw, **service_kw)

    def _is_cls_arg(self, arg):
        if not isinstance(arg, type):
            return False
        attr = getattr(arg, self._fn.__name__, None)
        if attr is None:
            return False
        return getattr(attr, '__self__', None) is arg

    def _add_constructor(self, t, creg_params, service_params):
        ctr = ActorTemplateCtr(
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_name=self._service_name,
            t=t,
            creg_params=creg_params,
            service_params=service_params,
            )
        self._ctr_collector.add_constructor(ctr)


class ServiceActorMarker:

    def __init__(self, system_probe, ctr_collector, module_name, service_name):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name

    def __call__(self, fn_or_t):
        if isinstance(fn_or_t, Type):
            # Type-specialized variant.
            return ServiceActorWrapper(self._ctr_collector, self._module_name, self._service_name, fn_or_t)
        elif type(fn_or_t) is classmethod:
            raise RuntimeError(
                f"Wrap this method first with marker and then with classmethod (classmethod should be first): {fn_or_t!r}"
                )
        else:
            # Not type-specialized variant.
            return ServiceActorProbe(self._system, self._ctr_collector, self._module_name, self._service_name, fn_or_t)


class ActorMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    def __getattr__(self, service_name):
        return ServiceActorMarker(self._system, self._ctr_collector, self._module_name, service_name)
