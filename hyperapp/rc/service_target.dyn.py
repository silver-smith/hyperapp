from dataclasses import dataclass

from . import htypes
from .services import (
    builtin_services,
    )
from .code.rc_requirement import Requirement
from .code.import_resource import ImportResource


# Unused. Is it really needed?`
@dataclass(frozen=True, unsafe_hash=True)
class ServiceFoundReq(Requirement):

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.service.service_found_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.service_found(self.service_name)

    def make_resource(self, target):
        raise NotImplementedError(f"ServiceFoundReq is never actually used: {self.service_name!r}")


@dataclass(frozen=True, unsafe_hash=True)
class ServiceCompleteReq(Requirement):

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.service.service_complete_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.service_complete(self.service_name)

    def make_resource(self, target):
        return ImportResource(['services', self.service_name], target.service_piece)


class ServiceFoundTarget:

    def __init__(self, service_name):
        self._service_name = service_name
        self._completed = False
        self._provider_resource_tgt = None
        self._attr_name = None
        self._import_alias_tgt = None

    @property
    def name(self):
        return f'service_found/{self._service_name}'

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        if self._import_alias_tgt:
            return {self._import_alias_tgt}
        else:
            return set()

    def update_status(self):
        if self._completed:
            return
        if self._provider_resource_tgt and self._provider_resource_tgt.completed:
            self._completed = True
        elif self._import_alias_tgt and self._import_alias_tgt.completed:
            self._completed = True

    def set_provider(self, resource_tgt, attr_name):
        self._provider_resource_tgt = resource_tgt
        self._attr_name = attr_name
        self._import_alias_tgt = resource_tgt.import_alias_tgt
        self.update_status()


class ServiceCompleteTarget:

    @staticmethod
    def target_name_for_service_name(service_name):
        return f'service_complete/{service_name}'

    def __init__(self, service_name, service_found_tgt):
        self._service_name = service_name
        self._service_found_tgt = service_found_tgt
        self._is_builtin = service_name in builtin_services
        self._completed = self._is_builtin

    @property
    def name(self):
        return self.target_name_for_service_name(self._service_name)

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        if self._is_builtin:
            return set()
        else:
            return {self._service_found_tgt}

    def update_status(self):
        pass

    @property
    def service_piece(self):
        if self._is_builtin:
            return htypes.builtin.builtin_service(self._service_name)
        else:
            assert 0, f'todo: {self._service_name}'
