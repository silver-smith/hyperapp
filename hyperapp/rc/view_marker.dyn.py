from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    )
from .code.actor_probe import ActorProbeBase
from .code.view_ctr import ViewTemplateCtr


class ViewProbe(ActorProbeBase):

    def _add_constructor(self, params, t):
        ctr = ViewTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=params.real_qual_name(self._fn),
            t=t,
            ctx_params=params.ctx_names,
            service_params=params.service_names,
            )
        self._ctr_collector.add_constructor(ctr)


def view_marker(fn, module_name, system, ctr_collector):
    check_not_classmethod(fn)
    check_is_function(fn)
    return ViewProbe(system, ctr_collector, module_name, fn)
