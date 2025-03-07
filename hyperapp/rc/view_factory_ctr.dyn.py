from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor
from .code.d_type import k_type


class ViewFactoryTemplateCtr(Constructor):

    _service_name = 'view_factory_reg'

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            model_t=pyobj_creg.invite_opt(piece.model_t),
            ui_t_t=pyobj_creg.invite_opt(piece.ui_t_t),
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            view_t=pyobj_creg.invite(piece.view_t),
            )

    def __init__(self, module_name, attr_qual_name, model_t, ui_t_t, ctx_params, service_params, view_t):
        self._module_name = module_name
        self._attr_qual_name = attr_qual_name
        self._model_t = model_t
        self._ui_t_t = ui_t_t
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._view_t = view_t
        self._view_resolved_tgt = None

    @property
    def piece(self):
        return htypes.view_factory_ctr.ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t=pyobj_creg.actor_to_ref_opt(self._model_t),
            ui_t_t=pyobj_creg.actor_to_ref_opt(self._ui_t_t),
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
        self._view_resolved_tgt = target_set.factory.config_item_resolved('view_reg', self._view_type_name)
        resolved_tgt.add_dep(self._view_resolved_tgt)
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
        k_t = k_type(types, self._module_name.split('.')[-1], name=self._attr_qual_name[-1])
        k = k_t()
        template = htypes.view_factory.template(
            k=mosaic.put(k),
            model_t=pyobj_creg.actor_to_ref_opt(self._model_t),
            ui_t_t=pyobj_creg.actor_to_ref_opt(self._ui_t_t),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            is_wrapper='inner' in self._ctx_params,
            view_ctx_params=self._view_resolved_tgt.constructor.ctx_params,
            system_fn=mosaic.put(system_fn),
            )
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.system-fn'] = system_fn
            name_to_res[f'{self._fn_name}.k'] = k
            name_to_res[f'{self._fn_name}.view-factory-template'] = template
        return template

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)

    @property
    def _view_type_name(self):
        return f'{self._view_t.module_name}-{self._view_t.name}'
