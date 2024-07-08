from dataclasses import dataclass

from . import htypes


@dataclass(frozen=True, unsafe_hash=True)
class TestedServiceReq:

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.test_target.tested_service_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.tested_service(self.service_name)
