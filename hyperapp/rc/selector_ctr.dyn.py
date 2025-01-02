from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr


class SelectorTemplateCtrBase(ModuleCtr):

    _service_name = 'selector_action'

    def __init__(self, module_name, attr_qual_name, service_params, value_t):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._service_params = service_params
        self._value_t = value_t

    def update_resource_targets(self, resource_tgt, target_set):
        ready_tgt = target_set.factory.config_item_ready(self._service_name, self._resource_name)
        resolved_tgt = target_set.factory.config_item_resolved(self._service_name, self._resource_name)
        ready_tgt.set_provider(resource_tgt)
        resolved_tgt.resolve(self)

    @property
    def _type_name(self):
        return f'{self._value_t.module_name}-{self._value_t.name}'

    @property
    def _resource_name(self):
        return f'{self._type_name}.selector.{self._action}'


class SelectorGetTemplateCtr(SelectorTemplateCtrBase):

    _action = 'get'

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
        assert 0, self._value_t


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
