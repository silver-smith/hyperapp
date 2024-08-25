import inspect

from .code.actor_ctr import ActorProbeCtr


class ServiceActorWrapper:

    def __init__(self, ctr_collector, module_name, service_name, t):
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name
        self._t = t

    def __call__(self, fn):
        qual_name = fn.__qualname__.split('.')
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
            params = params[1:]
        ctr = ActorProbeCtr(
            attr_qual_name=qual_name,
            service_name=self._service_name,
            t=self._t,
            params=params,
            )
        self._ctr_collector.add_constructor(ctr)
        return fn


class ServiceActorMarker:

    def __init__(self, ctr_collector, module_name, service_name):
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name

    def __call__(self, t):
        return ServiceActorWrapper(self._ctr_collector, self._module_name, self._service_name, t)


def actor_marker(service_name, module_name, ctr_collector):
    return ServiceActorMarker(ctr_collector, module_name, service_name)
