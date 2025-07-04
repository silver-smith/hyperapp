from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr
from .code.cfg_item_req import CfgItemReq
from .code.d_type import k_type


class MultiActorTemplateCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            t=pyobj_creg.invite(piece.t),
            creg_params=piece.creg_params,
            service_params=piece.service_params,
            )

    def __init__(self, module_name, attr_qual_name, service_name, t, creg_params, service_params):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._t = t
        self._creg_params = creg_params
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.actor_resource.multi_actor_template_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            t=pyobj_creg.actor_to_ref(self._t),
            creg_params=tuple(self._creg_params),
            service_params=tuple(self._service_params),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        req = CfgItemReq.from_actor(self._service_name, self._t)
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            self._service_name, self._resource_name, req,
            provider=resource_tgt,
            ctr=self,
            )
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.multi-actor-template']

    def make_component(self, types, python_module, name_to_res=None):
        object = python_module
        prefix = []
        for name in self._attr_qual_name:
            object = htypes.builtin.attribute(
                object=mosaic.put(object),
                attr_name=name,
                )
            if name_to_res is not None:
                name_to_res['.'.join([*prefix, name])] = object
            prefix.append(name)
        k_t = k_type(types, self._module_name.split('.')[-1], name=self._attr_qual_name[-1])
        k = k_t()
        template = htypes.system.multi_actor_template(
            k=mosaic.put(k),
            t=pyobj_creg.actor_to_ref(self._t),
            function=mosaic.put(object),
            service_params=tuple(self._service_params),
            )
        if name_to_res is not None:
            name_to_res[f'{self._resource_name}.k'] = k
            name_to_res[f'{self._resource_name}.multi-actor-template'] = template
        return template

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)

    @property
    def _resource_name(self):
        return self._fn_name
