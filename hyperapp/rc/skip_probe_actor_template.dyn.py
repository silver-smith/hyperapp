from .services import (
    pyobj_creg,
    )
from .code.system import ActorTemplate
from .code.actor_probe import ActorProbe


# When calling probe from resolved actor template, service params are passed.
# But probe expects they are not. As a result, probe records all parameters
# as non-service (other, ctx) parameters.

# Do not resolve function in contstructor.
# It is called during system configuration, when markers are not yet initialized.

class SkipProbeActorTemplate(ActorTemplate):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            fn_ref=piece.function,
            service_params=piece.service_params,
            )

    def __init__(self, t, fn_ref, service_params):
        super().__init__(t, self._wrapper, service_params)
        self._real_fn_ref = fn_ref

    @property
    def piece(self):
        return htypes.skip_probe_actor_template.skip_probe_actor_template(
            t=pyobj_creg.actor_to_ref(self.t),
            function=self._real_fn_ref,
            service_params=tuple(self._service_params),
            )

    def _wrapper(self, *args, **kw):
        real_fn = pyobj_creg.invite(self._real_fn_ref)
        probe = getattr(real_fn, '__func__', None)
        if isinstance(probe, ActorProbe):
            fn = probe.real_fn
            args = (real_fn.__self__, *args)
        else:
            fn = real_fn
        return fn(*args, **kw)
