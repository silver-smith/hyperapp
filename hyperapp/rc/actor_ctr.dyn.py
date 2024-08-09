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



class ActorTemplateCtrBase(Constructor):

    def __init__(self, t):
        self._t = t

    def get_component(self, name_to_res):
        return name_to_res[f'{self._type_name}.actor-template']

    @property
    def _type_name(self):
        return f'{self._t.module_name}_{self._t.name}'


class CoreActorTemplateCtr(ActorTemplateCtrBase):

    @classmethod
    def from_template_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            )


class ActorTemplateCtr(ActorTemplateCtrBase):

    @classmethod
    def from_rec(cls, service_name, t, rec):
        return cls(
            attr_qual_name=rec.attr_qual_name,
            service_name=service_name,
            t=t,
            creg_params=rec.creg_params,
            service_params=rec.service_params,
            )

    @classmethod
    def from_piece(cls, piece):
        return cls(
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            t=pyobj_creg.invite(piece.t),
            creg_params=piece.creg_params,
            service_params=piece.service_params,
            )

    def __init__(self, attr_qual_name, service_name, t, creg_params, service_params):
        super().__init__(t)
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._creg_params = creg_params
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.rc_constructors.actor_template(
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            t=pyobj_creg.actor_to_ref(self._t),
            creg_params=tuple(self._creg_params),
            service_params=tuple(self._service_params),
            )

    def update_targets(self, target_set):
        resolved_tgt = target_set.factory.config_item_resolved(self._service_name, self._type_name)
        resolved_tgt.resolve(self)
        target_set.update_deps_for(resolved_tgt)

    def make_component(self, python_module, name_to_res=None):
        object = python_module
        prefix = []
        for name in self._attr_qual_name:
            object = htypes.builtin.attribute(
                object=mosaic.put(object),
                attr_name=name,
                )
            if name_to_res is not None:
                name_to_res['.'.join(*prefix, name)] = object
            prefix.append(name)
        template = htypes.system.actor_template(
            t=pyobj_creg.actor_to_ref(self._t),
            function=mosaic.put(object),
            service_params=tuple(self._service_params),
            )
        if name_to_res is not None:
            name_to_res[f'{self._type_name}.actor-template'] = template
        return service
