from dataclasses import dataclass

from . import htypes
from .code.rc_target import Target
from .code.rc_requirement import Requirement
from .code.import_resource import ImportResource


@dataclass(frozen=True, unsafe_hash=True)
class BuiltinServiceReq(Requirement):

    required_by_module_name: str
    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(
            required_by_module_name=piece.required_by_module_name,
            service_name=piece.service_name,
            )

    @property
    def piece(self):
        return htypes.builtin_service.builtin_service_req(
            required_by_module_name=self.required_by_module_name,
            service_name=self.service_name,
            )

    @property
    def is_builtin(self):
        return True

    def get_target(self, target_factory):
        return target_factory.builtin_service(self.service_name)

    def make_resource(self, target):
        return ImportResource(self.required_by_module_name, ['services', self.service_name], target.service_piece)


class BuiltinServiceTarget(Target):

    @staticmethod
    def target_name_for_service_name(service_name):
        return f'builtin_service/{service_name}'

    def __init__(self, service_name):
        self._service_name = service_name

    @property
    def name(self):
        return self.target_name_for_service_name(self._service_name)

    @property
    def completed(self):
        return True

    @property
    def service_piece(self):
        return htypes.builtin.builtin_service(self._service_name)
