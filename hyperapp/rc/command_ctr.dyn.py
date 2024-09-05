from . import htypes
from .code.actor_ctr import ActorTemplateCtr


class CommandTemplateCtr(ActorTemplateCtr):

    _piece_t = htypes.command_resource.command_template_ctr

    @property
    def _resource_name(self):
        attr_name = '_'.join(self._attr_qual_name)
        return f'{self._t.module_name}_{self._t.name}_{attr_name}'
