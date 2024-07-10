from dataclasses import dataclass

from . import htypes
from .code.requirement import Requirement


@dataclass(frozen=True, unsafe_hash=True)
class TestedServiceReq(Requirement):

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.test_target.tested_service_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.tested_service(self.service_name)


@dataclass(frozen=True, unsafe_hash=True)
class TestedCodeReq(Requirement):

    code_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.code_name)

    @property
    def piece(self):
        return htypes.test_target.tested_code_req(self.code_name)

    def get_target(self, target_factory):
        return target_factory.python_module_imported(self.code_name)

    def get_tested_target(self, target_factory):
        return target_factory.python_module_resource_by_code_name(self.code_name)
