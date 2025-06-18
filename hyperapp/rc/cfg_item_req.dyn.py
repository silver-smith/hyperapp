from functools import cached_property

from hyperapp.boot.htypes import Type

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_requirement import Requirement
from .code.config_item_resource import ConfigItemResource


class CfgItemReq(Requirement):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            service_name=piece.service_name,
            actor=web.summon(piece.actor),
            tested_modules=piece.tested_modules,
            )

    @classmethod
    def from_actor(cls, service_name, t_or_data, tested_modules=None):
        if isinstance(t_or_data, Type):
            actor = pyobj_creg.actor_to_piece(t_or_data)
        else:
            actor = t_or_data
        return cls(service_name, actor, tested_modules)

    def __init__(self, service_name, actor, tested_modules=None):
        self._service_name = service_name
        self._actor = actor
        self._tested_modules = tuple(tested_modules or [])

    def __str__(self):
        return f"CfgItemReq(service_name={self._service_name}, actor={self._actor} / {self._tested_modules})"

    def __eq__(self, rhs):
        return (type(rhs) == CfgItemReq
                and rhs._service_name == self._service_name
                and rhs._actor == self._actor
                and rhs._tested_modules == self._tested_modules)

    def __hash__(self):
        return hash(('action_req', self._service_name, self._actor, self._tested_modules))

    @property
    def piece(self):
        return htypes.actor_resource.cfg_item_req(
            service_name=self._service_name,
            actor=mosaic.put(self._actor),
            tested_modules=self._tested_modules,
            )

    @cached_property
    def desc(self):
        if isinstance(self._actor, htypes.builtin.record_mt):
            actor = f'{self._actor.module_name}-{self._actor.name}'
        elif isinstance(self._actor, htypes.builtin.builtin_mt):
            actor = self._actor.name
        else:
            actor = self._actor
        return f"{self._service_name}:{actor} actor"

    def get_target(self, target_factory):
        resolved_tgt = target_factory.config_item_resolved(self._service_name, self._key_name)
        if not resolved_tgt.completed:
            return resolved_tgt
        if resolved_tgt.provider_resource_tgt.module_name in self._tested_modules:
            return resolved_tgt
        else:
            return target_factory.config_item_complete(self._service_name, self._key_name, self)

    def make_resource(self, target):
        resource_tgt = target.provider_resource_tgt
        if resource_tgt.module_name in self._tested_modules:
            import_tgt = resource_tgt.import_tgt
            _module_name, _recorder_piece, python_module = import_tgt.recorded_python_module(tag='test')
            template_piece = target.constructor.make_component(import_tgt.types, python_module)
        else: 
            assert resource_tgt.completed
            template_piece = resource_tgt.get_resource_component(target.constructor)
        return ConfigItemResource(
            service_name=self._service_name,
            template_ref=mosaic.put(template_piece),
            )

    @property
    def _key_name(self):
        if isinstance(self._actor, htypes.builtin.record_mt):
            return f'{self._actor.module_name}-{self._actor.name}'
        elif isinstance(self._actor, htypes.builtin.builtin_mt):
            return self._actor.name
        else:
            return str(self._actor)
