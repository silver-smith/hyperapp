from .services import (
    deduce_t,
    pyobj_creg,
    web,
    )
from .code.actor_ctr import ActorTemplateCtr
from .code.marker_utils import split_params


class ActorProbeBase:

    def __init__(self, system_probe, ctr_collector, module_name, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._fn = fn
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

    @property
    def real_fn(self):
        return self._fn

    def __call__(self, *args, **kw):
        params = split_params(self._fn, args, kw)
        if len(params.ctx_names) < 1:
            raise RuntimeError(f"First parameter expected to be a piece: {self._fn!r}")
        piece = params.values[params.ctx_names[0]]
        if self._t is None:
            t = deduce_t(piece)
        else:
            t = self._t
        self._add_constructor(params, t)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in params.service_names
            }
        return self._fn(*args, **kw, **service_kw)


class ActorProbe(ActorProbeBase):

    def __init__(self, system_probe, ctr_collector, module_name, service_name, fn, t=None):
        super().__init__(system_probe, ctr_collector, module_name, fn)
        self._service_name = service_name
        self._t = t

    def _add_constructor(self, params, t):
        ctr = ActorTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_name=self._service_name,
            t=t,
            creg_params=params.ctx_names,
            service_params=params.service_names,
            )
        self._ctr_collector.add_constructor(ctr)


class ActorProbeTemplate:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            fn_piece=web.summon(piece.function),
            )

    def __init__(self, t, fn_piece):
        self._t = t
        self._fn = fn_piece

    def __repr__(self):
        return f"<ActorProbeTemplate {self._t}: {self._fn}>"

    @property
    def key(self):
        return self._t

    def resolve(self, system, service_name):
        fn = pyobj_creg.animate(self._fn)
        assert (
            isinstance(fn, ActorProbe)
            or hasattr(fn, '__self__') and isinstance(fn.__func__, ActorProbe)
            ) , repr(fn)
        return fn
