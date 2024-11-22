from .services import (
    pyobj_creg,
    )
from .code.system import ActorTemplate
from .code.actor_probe import ActorProbe


# When calling probe from resolved actor template, service params are passed.
# But probe expects they are not. As a result, probe records all parameters
# as non-service (other, ctx) parameters.

class SkipProbeActorTemplate(ActorTemplate):

    def __init__(self, t, fn, service_params):
        super().__init__(t, self._wrapper, service_params)
        self._real_fn = fn

    @property
    def piece(self):
        return htypes.skip_probe_actor_template.skip_probe_actor_template(
            t=pyobj_creg.actor_to_ref(self.t),
            function=pyobj_creg.actor_to_ref(self._fn),
            service_params=tuple(self._service_params),
            )

    def _wrapper(self, *args, **kw):
        probe = getattr(self._real_fn, '__func__', None)
        if isinstance(probe, ActorProbe):
            fn = probe.real_fn
            args = (self._real_fn.__self__, *args)
        else:
            fn = self._real_fn
        return fn(*args, **kw)
