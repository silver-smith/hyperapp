from dataclasses import dataclass

from . import htypes


@dataclass(frozen=True, unsafe_hash=True)
class ServiceCompleteReq:

    service_name: str

    @property
    def piece(self):
        return htypes.service.service_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.service_complete(self.service_name)


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
