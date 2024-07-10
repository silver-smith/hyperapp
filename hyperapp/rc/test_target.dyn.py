from dataclasses import dataclass

from . import htypes
from .code.import_resource import ImportResource
from .code.requirement import Requirement
from .code.test_job import TestJob


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


class TestTarget:

    def __init__(self, python_module_src, type_src_list, function, req_to_target, idx=1):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._function = function
        self._req_to_target = req_to_target or {}
        self._idx = idx
        self._completed = False
        self._ready = False

    @property
    def name(self):
        return f'test/{self._python_module_src.name}/{self._function.name}/{self._idx}'

    @property
    def ready(self):
        return self._ready

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return self._req_to_target.values()

    def update_status(self):
        self._ready = all(target.completed for target in self._req_to_target.values())

    def make_job(self):
        resources = [
            ImportResource.from_type_src(src)
            for src in self._type_src_list
            ]
        return TestJob(self._python_module_src, self._idx, resources)

    def handle_job_result(self, target_set, result):
        self._completed = True
