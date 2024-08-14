from hyperapp.common.htypes import Type

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.rc_requirement import Requirement
from .code.config_item_resource import ConfigItemResource


class ActorReq(Requirement):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        return cls(
            cfg_item_creg=cfg_item_creg,
            service_name=piece.service_name,
            t=pyobj_creg.invite(piece.t),
            )

    def __init__(self, cfg_item_creg, service_name, t):
        self._cfg_item_creg = cfg_item_creg
        self._service_name = service_name
        self._t = t

    def __str__(self):
        return f"ActorReq(service_name={self._service_name}, t={self._t})"

    def __eq__(self, rhs):
        return (type(rhs) == ActorReq
                and rhs._service_name == self._service_name
                and rhs._t == self._t)

    def __hash__(self):
        return hash(('action_req', self._service_name, self._t))

    @property
    def piece(self):
        return htypes.actor_resource.actor_req(
            service_name=self._service_name,
            t=pyobj_creg.actor_to_ref(self._t),
            )

    def get_target(self, target_factory):
        return target_factory.config_item_complete(self._service_name, self._type_name)

    def make_resource(self, target):
        resource_tgt = target.provider_resource_tgt
        template_piece = resource_tgt.get_resource(target.constructor)
        cfg_item = self._cfg_item_creg.animate(template_piece, self._service_name)
        return ConfigItemResource(
            service_name=self._service_name,
            cfg_item=cfg_item,
            )

    @property
    def _type_name(self):
        return f'{self._t.module_name}_{self._t.name}'
