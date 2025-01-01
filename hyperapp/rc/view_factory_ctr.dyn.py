from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor
from .code.d_type import d_type


class ViewFactoryTemplateCtr(Constructor):

    _service_name = 'view_factory_reg'

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            view_t=pyobj_creg.invite(piece.view_t),
            )

    def __init__(self, module_name, attr_qual_name, ctx_params, service_params, view_t):
        self._module_name = module_name
        self._attr_qual_name = attr_qual_name
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._view_t = view_t

    @property
    def piece(self):
        return htypes.view_factory_ctr.ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            )

    def update_targets(self, target_set):
        resource_tgt = target_set.factory.python_module_resource_by_module_name(self._module_name)
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            self._service_name, self._fn_name,
            provider=resource_tgt,
            ctr=self,
            )
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[f'{self._fn_name}.view-factory-template']

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
        d_t = d_type(types, self._module_name.split('.')[-1], name=self._attr_qual_name[-1])
        d = d_t()
        template = htypes.view_factory.template(
            d=mosaic.put(d),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            is_wrapper='inner' in self._ctx_params,
            system_fn=mosaic.put(system_fn),
            )
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.system-fn'] = system_fn
            name_to_res[f'{self._fn_name}.d'] = d
            name_to_res[f'{self._fn_name}.view-factory-template'] = template
        return template

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)
