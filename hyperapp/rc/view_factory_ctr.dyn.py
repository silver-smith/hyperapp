from hyperapp.boot.htypes import TPrimitive, TOptional, TRecord

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr
from .code.d_type import k_type


class ViewFactoryTemplateSingleModelCtr(ModuleCtr):

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
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._model_t = model_t
        self._ui_t_t = ui_t_t
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._view_t = view_t
        self._view_resolved_tgt = None

    @property
    def piece(self):
        return htypes.view_factory_ctr.single_model_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t=pyobj_creg.actor_to_ref_opt(self._model_t),
            ui_t_t=pyobj_creg.actor_to_ref_opt(self._ui_t_t),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        _, resolved_tgt, _ = target_set.factory.config_items(
            self._service_name, self._fn_name,
            provider=resource_tgt,
            )
        multi_ctr = resolved_tgt.non_complete_constructor
        if multi_ctr is None:
            multi_ctr = ViewFactoryTemplateMultiModelCtr(
                module_name=self._module_name,
                attr_qual_name=self._attr_qual_name,
                ui_t_t=self._ui_t_t,
                ctx_params=self._ctx_params,
                service_params=self._service_params,
                view_t=self._view_t,
                )
            multi_ctr.init_view_factory_targets(resource_tgt, target_set, resolved_tgt)
        if self._model_t is not None:
            multi_ctr.add_model_t(self._model_t)

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)


class ViewFactoryTemplateMultiModelCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece):
        if piece.model_t_list is not None:
            model_t_list = [
                pyobj_creg.invite(model_t) for model_t in piece.model_t_list
                ]
        else:
            model_t_list = None
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            ui_t_t=pyobj_creg.invite_opt(piece.ui_t_t),
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            view_t=pyobj_creg.invite(piece.view_t),
            model_t_list=model_t_list,
            )

    def __init__(self, module_name, attr_qual_name, ui_t_t, ctx_params, service_params, view_t, model_t_list=None):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._ui_t_t = ui_t_t
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._view_t = view_t
        self._view_resolved_tgt = None
        self._model_t_set = set(model_t_list) if model_t_list is not None else None

    @property
    def piece(self):
        return htypes.view_factory_ctr.multi_model_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t_list=self._model_t_list_field,
            ui_t_t=pyobj_creg.actor_to_ref_opt(self._ui_t_t),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            )

    @property
    def _model_t_list_field(self):
        if self._model_t_set is None:
            return None
        return tuple(sorted(
            pyobj_creg.actor_to_ref(model_t) for model_t in self._model_t_set
            ))

    def init_view_factory_targets(self, resource_tgt, target_set, resolved_tgt):
        self._view_resolved_tgt = target_set.factory.config_item_resolved('view_reg', self._view_type_name)
        resolved_tgt.add_dep(self._view_resolved_tgt)
        resolved_tgt.resolve(self)
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def add_model_t(self, model_t):
        if self._model_t_set is not None:
            self._model_t_set.add(model_t)
        else:
            self._model_t_set = {model_t}

    def get_component(self, name_to_res):
        return name_to_res[f'{self._fn_name}.view-factory-cfg-item']

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
            model_t_list=self._model_t_list_field,
            ui_t_t=pyobj_creg.actor_to_ref_opt(self._ui_t_t),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            is_wrapper='inner' in self._ctx_params,
            view_ctx_params=self._view_resolved_tgt.constructor.ctx_params,
            system_fn=mosaic.put(system_fn),
            )
        cfg_item = htypes.cfg_item.data_cfg_item(
            key=mosaic.put(k),
            value=mosaic.put(template),
            )
        if name_to_res is not None:
            for model_t in self._model_t_set or []:
                self._add_complex_type(model_t, name_to_res)
            name_to_res[f'{self._fn_name}.system-fn'] = system_fn
            name_to_res[f'{self._fn_name}.k'] = k
            name_to_res[f'{self._fn_name}.view-factory-template'] = template
            name_to_res[f'{self._fn_name}.view-factory-cfg-item'] = cfg_item
        return template

    def _add_complex_type(self, t, name_to_res):
        if isinstance(t, TOptional):
            assert isinstance(t.base_t, (TRecord, TPrimitive)), t.base_t
            name = f'{t.base_t.module_name}-{t.base_t.name}-opt'
            mt = pyobj_creg.actor_to_piece(t)
            name_to_res[name] = mt

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)

    @property
    def _view_type_name(self):
        return f'{self._view_t.module_name}-{self._view_t.name}'
