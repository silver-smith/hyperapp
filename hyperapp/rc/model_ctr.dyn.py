from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_constructor import ModuleCtr
from .code.cfg_item_req import CfgItemReq


class ModelCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            model_t=pyobj_creg.invite(piece.model_t),
            ui_t=web.summon(piece.ui_t),
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            )

    def __init__(self, module_name, attr_qual_name, model_t, ui_t, ctx_params, service_params):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._model_t = model_t
        self._ui_t = ui_t
        self._ctx_params = ctx_params
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.model_resource.model_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            ui_t=mosaic.put(self._ui_t),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        req = CfgItemReq('visualizer_reg', self._model_t)
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            'visualizer_reg', self._resource_name, req, provider=resource_tgt, ctr=self)
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.model-cfg-item']

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
        model = htypes.model.model(
            ui_t=mosaic.put(self._ui_t),
            system_fn=mosaic.put(system_fn),
            )
        cfg_item = htypes.cfg_item.typed_cfg_item(
            t=pyobj_creg.actor_to_ref(self._model_t),
            value=mosaic.put(model),
            )
        if name_to_res is not None:
            name_to_res[f'{self._resource_name}.{self._ui_t_name}'] = self._ui_t
            name_to_res[f'{self._resource_name}.system-fn'] = system_fn
            name_to_res[f'{self._resource_name}.model'] = model
            name_to_res[f'{self._resource_name}.model-cfg-item'] = cfg_item
        return cfg_item

    @property
    def _resource_name(self):
        return f'{self._model_t.module_name}-{self._model_t.name}'

    @property
    def _ui_t_name(self):
        # Here we assume that ui_t is a record.
        return self._ui_t._t.name.replace('_', '-')
