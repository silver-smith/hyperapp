from hyperapp.boot.htypes import Type

from .code.actor_probe import ActorProbeBase
from .code.multi_actor_ctr import MultiActorTemplateCtr
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    )


class MultiActorProbe(ActorProbeBase):

    def __init__(self, system_probe, ctr_collector, module_name, service_name, fn, t=None):
        super().__init__(system_probe, ctr_collector, module_name, fn, t)
        self._service_name = service_name

    def _add_constructor(self, params, t):
        ctr = MultiActorTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=self.real_fn.__qualname__.split('.'),
            service_name=self._service_name,
            t=t,
            creg_params=params.ctx_names,
            service_params=params.service_names,
            )
        self._ctr_collector.add_constructor(ctr)


class MultiActorDecorator:

    def __init__(self, system_probe, ctr_collector, module_name, service_name):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name

    def __call__(self, fn):
        if isinstance(fn, Type):
            raise RuntimeError(f"Type-specialized decorators for multi_actors are not supported")
        check_not_classmethod(fn)
        check_is_function(fn)
        # Not type-specialized variant  (@mark.actor.my_registry).
        return MultiActorProbe(self._system, self._ctr_collector, self._module_name, self._service_name, fn)


class MultiActorMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    def __getattr__(self, service_name):
        return MultiActorDecorator(self._system, self._ctr_collector, self._module_name, service_name)
