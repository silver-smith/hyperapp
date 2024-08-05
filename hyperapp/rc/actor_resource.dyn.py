from dataclasses import dataclass

from hyperapp.common.htypes import Type

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_requirement import Requirement
# from .code.rc_resource import Resource


@dataclass(frozen=True, unsafe_hash=True)
class ActorReq(Requirement):

    service_name: str
    t: Type

    @classmethod
    def from_piece(cls, piece):
        return cls(
            service_name=piece.service_name,
            t=pyobj_creg.invite(piece.t),
            )

    @property
    def piece(self):
        return htypes.actor_resource.actor_req(
            service_name=self.service_name,
            t=pyobj_creg.actor_to_ref(self.t),
            )

    def get_target(self, target_factory):
        return target_factory.config_item_complete(self.service_name, self._type_name)

    def make_resource(self, target):
        assert 0, f"todo: {self}: {target}"

    @property
    def _type_name(self):
        return f'{self.t.module_name}_{self.t.name}'
