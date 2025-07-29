from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_constructor import Constructor, ModuleCtr
from .code.init_hook_req import InitHookReq


class BaseInitHookCtr(Constructor):

    @classmethod
    def from_template_piece(cls, piece, service_name, var_name):
        return cls(var_name)

    def __init__(self, var_name):
        self._var_name = var_name

    def get_component(self, name_to_res):
        return name_to_res[self._var_name]

    @property
    def _fn_name(self):
        return self._var_name.rsplit('.', 1)[0]  # Drop .hook suffix.

    @property
    def key(self):
        return self._fn_name

    @property
    def req(self):
        return InitHookReq(self._fn_name)



class InitHookCtr(ModuleCtr):

    _service_name = 'init_hook'

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.module_name, piece.attr_qual_name, piece.service_params)

    def __init__(self, module_name, attr_qual_name, service_params):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.init_hook_ctr.init_hook_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_params=tuple(self._service_params),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        req = InitHookReq(self._fn_name)
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            self._service_name, self._config_name, req,
            provider=resource_tgt,
            ctr=self,
            )
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[f'{self._fn_name}.hook']

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
            ctx_params=(),
            service_params=tuple(self._service_params),
            )
        template = htypes.cfg_item.fn_value_template(
            system_fn=mosaic.put(system_fn),
            )
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.system-fn'] = system_fn
            name_to_res[f'{self._fn_name}.hook'] = template
        return template

    @property
    def _config_name(self):
        return f'{self._module_name}-{self._fn_name}'

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)
