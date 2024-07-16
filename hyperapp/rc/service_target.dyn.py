from dataclasses import dataclass

from . import htypes
from .code.rc_requirement import Requirement


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
        assert 0, 'todo'


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
        assert 0, f'{self.service_name} / {target.name}'


class ServiceFoundTarget:

    def __init__(self, service_name):
        self._service_name = service_name
        self._completed = False
        self._provider_resource_tgt = None
        self._attr_name = None

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
        return []

    def update_status(self):
        pass

    def set_provider(self, resource_tgt, attr_name):
        self._provider_resource_tgt = resource_tgt
        self._attr_name = attr_name
        self._completed = True


class ServiceCompleteTarget:

    def __init__(self, service_name):
        self._service_name = service_name
        self._completed = False

    @property
    def name(self):
        return f'service_complete/{self._service_name}'

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return []

    def update_status(self):
        pass
