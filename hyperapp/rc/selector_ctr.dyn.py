from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor, ModuleCtr
from .code.cfg_item_req import CfgItemReq


_ACTION_SERVICE_NAME = 'selector_action'


def _action_resource_name(type_name, action):
    return f'{type_name}.selector.{action}'


class SelectorTemplateCtrBase(ModuleCtr):

    def __init__(self, module_name, attr_qual_name, service_params, value_t):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._service_params = service_params
        self._value_t = value_t

    def update_resource_targets(self, resource_tgt, target_set):
        ready_tgt = target_set.factory.config_item_ready(_ACTION_SERVICE_NAME, self._resource_name)
        resolved_tgt = target_set.factory.config_item_resolved(_ACTION_SERVICE_NAME, self._resource_name)
        ready_tgt.set_provider(resource_tgt)
        resolved_tgt.resolve(self)

    def make_function(self, types, python_module, name_to_res):
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
        name_to_res[f'{self._resource_name}.system-fn'] = system_fn
        return system_fn

    @property
    def _type_name(self):
        return f'{self._value_t.module_name}-{self._value_t.name}'

    @property
    def _resource_name(self):
        return _action_resource_name(self._type_name, self._action)


class SelectorGetTemplateCtr(SelectorTemplateCtrBase):

    _action = 'get'
    _ctx_params = ['value']

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            service_params=piece.service_params,
            value_t=pyobj_creg.invite(piece.value_t),
            )

    @property
    def piece(self):
        return htypes.selector_ctr.get_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_params=tuple(self._service_params),
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        super().update_resource_targets(resource_tgt, target_set)
        self._add_selector_ctr(resource_tgt, target_set)

    def _add_selector_ctr(self, resource_tgt, target_set):
        ctr = SelectorCtr(self._value_t)
        ctr.update_selector_targets(resource_tgt, target_set)


class SelectorPutTemplateCtr(SelectorTemplateCtrBase):

    _action = 'put'

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
        super().__init__(module_name, attr_qual_name, service_params, value_t)
        self._ctx_params = ctx_params

    @property
    def piece(self):
        return htypes.selector_ctr.put_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            )


class SelectorCtr(Constructor):

    def __init__(self, value_t):
        self._value_t = value_t
        self._get_resolved_tgt = None
        self._put_resolved_tgt = None

    def update_selector_targets(self, resource_tgt, target_set):
        self._get_resolved_tgt = target_set.factory.config_item_resolved(
            _ACTION_SERVICE_NAME, _action_resource_name(self._type_name, 'get'))
        self._put_resolved_tgt = target_set.factory.config_item_resolved(
            _ACTION_SERVICE_NAME, _action_resource_name(self._type_name, 'put'))
        service_name = 'selector_reg'
        req = CfgItemReq(service_name, self._value_t)
        _, resolved_tgt, _ = target_set.factory.config_items(
            service_name, self._type_name, req, provider=resource_tgt, ctr=self)
        resolved_tgt.add_dep(self._get_resolved_tgt)
        resolved_tgt.add_dep(self._put_resolved_tgt)
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[f'{self._type_name}.selector']

    def make_component(self, types, python_module, name_to_res):
        get_fn = self._get_resolved_tgt.constructor.make_function(
            types, python_module, name_to_res)
        put_fn = self._put_resolved_tgt.constructor.make_function(
            types, python_module, name_to_res)
        selector = htypes.selector.selector(
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            get_fn=mosaic.put(get_fn),
            put_fn=mosaic.put(put_fn),
            )
        name_to_res[f'{self._type_name}.selector'] = selector

    @property
    def _type_name(self):
        return f'{self._value_t.module_name}-{self._value_t.name}'
