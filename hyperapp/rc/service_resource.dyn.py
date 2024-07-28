from dataclasses import dataclass

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.rc_requirement import Requirement


@dataclass(frozen=True, unsafe_hash=True)
class ServiceReq(Requirement):

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.service_resource.service_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.config_item_complete('system', self.service_name)

    def make_resource(self, target):
        assert 0, target
