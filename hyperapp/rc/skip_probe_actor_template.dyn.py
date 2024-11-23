import inspect

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

    @property
    def piece(self):
        return htypes.skip_probe_actor_template.skip_probe_actor_template(
            t=pyobj_creg.actor_to_ref(self.t),
            function=self._fn_ref,
            service_params=tuple(self._service_params),
            )

    def resolve(self, system, service_name):
        fn = pyobj_creg.invite(self._fn_ref)
        if inspect.ismethod(fn):
            probe = fn.__func__
            if isinstance(probe, ActorProbe):
                obj = fn.__self__
                fn = probe.real_fn.__get__(obj)
        return self._resolve_services(fn, system)
