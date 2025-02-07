from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor
from .code.cfg_item_req import CfgItemReq


class ViewTemplateCtr(Constructor):

    _service_name = 'view_reg'

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            t=pyobj_creg.invite(piece.t),
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            )

    def __init__(self, module_name, attr_qual_name, t, ctx_params, service_params):
        self._module_name = module_name
        self._attr_qual_name = attr_qual_name
        self._t = t
        self._ctx_params = ctx_params
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.view_ctr.template_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            t=pyobj_creg.actor_to_ref(self._t),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

    def update_targets(self, target_set):
        resource_tgt = target_set.factory.python_module_resource_by_module_name(self._module_name)
        req = CfgItemReq(self._service_name, self._t)
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            self._service_name, self._type_name, req,
            provider=resource_tgt,
            ctr=self,
            )
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[f'{self._type_name}.view-template']

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
        system_fn = htypes.system_fn.ctx_fn(
            function=mosaic.put(object),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )
        template = htypes.cfg_item.typed_fn_cfg_item(
            t=pyobj_creg.actor_to_ref(self._t),
            system_fn=mosaic.put(system_fn),
            )
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.system-fn'] = system_fn
            name_to_res[f'{self._type_name}.view-template'] = template
        return template

    @property
    def ctx_params(self):
        return self._ctx_params

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)

    @property
    def _type_name(self):
        return f'{self._t.module_name}-{self._t.name}'
