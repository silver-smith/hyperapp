from dataclasses import dataclass

from . import htypes


# Unused. Is it really needed?`
@dataclass(frozen=True, unsafe_hash=True)
class ServiceFoundReq:

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.service.service_found_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.service_found(self.service_name)


@dataclass(frozen=True, unsafe_hash=True)
class ServiceCompleteReq:

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.service.service_complete_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.service_complete(self.service_name)


class ServiceFoundTarget:

    def __init__(self, service_name):
        self._service_name = service_name
        self._completed = False

    @property
    def name(self):
        return f'service_found/{self._service_name}'

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed


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
