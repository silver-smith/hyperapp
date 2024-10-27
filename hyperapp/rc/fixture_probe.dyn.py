import inspect

from .services import (
    pyobj_creg,
    web,
    )
from .code.system_probe import Probe, resolve_service_fn


class FixtureProbe(Probe):

    def __init__(self, system_probe, service_name, ctl_ref, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._ctl_ref = ctl_ref

    def __repr__(self):
        return f"<FixtureProbe {self._fn} {self._params} {self._ctl_ref}>"


class FixtureTemplateBase:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            service_name=piece.service_name,
            ctl_ref=piece.ctl,
            fn_piece=web.summon(piece.function),
            params=piece.params,
            )

    def __init__(self, service_name, ctl_ref, fn_piece, params):
        self._service_name = service_name
        self._ctl_ref = ctl_ref
        self._fn = fn_piece
        self._params = params

    @property
    def key(self):
        return self._service_name

    @property
    def ctl_ref(self):
        return self._ctl_ref


class FixtureObjTemplate(FixtureTemplateBase):

    def __repr__(self):
        return f"<FixtureObjTemplate {self._fn} {self._params}>"

    def resolve(self, system, service_name):
        fn = pyobj_creg.animate(self._fn)
        want_config, service_params, free_params, is_gen, service = resolve_service_fn(
            system, service_name, fn, self._params, self._params, args=[], kw={})
        if inspect.iscoroutine(service):
            service = system.run_async_coroutine(service)
        return service


class FixtureProbeTemplate(FixtureTemplateBase):

    def __repr__(self):
        return f"<FixtureProbeTemplate {self._fn} {self._params}>"

    def resolve(self, system, service_name):
        fn = pyobj_creg.animate(self._fn)
        probe = FixtureProbe(system, service_name, self._ctl_ref, fn, self._params)
        probe.apply_if_no_params()
        return probe
