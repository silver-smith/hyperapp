from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr


class EditorDefaultTemplateCtr(ModuleCtr):

    _service_name = 'editor_default_reg'

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            value_t=pyobj_creg.invite(piece.value_t),
            )

    def __init__(self, module_name, attr_qual_name, ctx_params, service_params, value_t):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._value_t = value_t

    @property
    def piece(self):
        return htypes.editor_ctr.default_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            self._service_name, self._resource_name,
            provider=resource_tgt,
            ctr=self,
            )
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.cfg-item']

    def make_component(self, types, python_module, name_to_res):
        object = python_module
        prefix = []
        for name in self._attr_qual_name:
            object = htypes.builtin.attribute(
                object=mosaic.put(object),
                attr_name=name,
                )
            name_to_res['.'.join([*prefix, name])] = object
            prefix.append(name)
        system_fn = htypes.system_fn.ctx_fn(
            function=mosaic.put(object),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )
        cfg_item = htypes.cfg_item.typed_cfg_item(
            t=pyobj_creg.actor_to_ref(self._value_t),
            value=mosaic.put(system_fn),
            )
        name_to_res[f'{self._fn_name}.system-fn'] = system_fn
        name_to_res[f'{self._resource_name}.cfg-item'] = cfg_item
        return cfg_item

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)

    @property
    def _type_name(self):
        return f'{self._value_t.module_name}-{self._value_t.name}'

    @property
    def _resource_name(self):
        return f'{self._type_name}.editor_default'
