from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor
from .code.actor_probe_resource import ActorProbeResource


class ActorProbeCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            t=pyobj_creg.invite(piece.t),
            params=piece.params,
            )

    def __init__(self, attr_qual_name, service_name, t, params):
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._t = t
        self._params = params

    def update_resource_targets(self, resource_tgt, target_set):
        resource_tgt.import_alias_tgt.add_component(self)
        ready_tgt = target_set.factory.config_item_ready(self._service_name, self._type_name)
        ready_tgt.set_provider(resource_tgt, target_set)
        resolved_tgt = target_set.factory.config_item_resolved(self._service_name, self._type_name)
        resource_tgt.add_cfg_item_target(resolved_tgt)
        target_set.update_deps_for(ready_tgt)
        target_set.update_deps_for(resource_tgt)

    def make_component(self, python_module, name_to_res=None):
        object = python_module
        for name in self._attr_qual_name:
            object = htypes.builtin.attribute(
                object=mosaic.put(object),
                attr_name=name,
                )
        return object

    def make_resource(self, module_name, python_module):
        return ActorProbeResource(self._attr_qual_name, self._service_name, self._t, self.make_component(python_module), self._params)

    @property
    def _type_name(self):
        return f'{self._t.module_name}_{self._t.name}'
