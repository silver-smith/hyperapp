from dataclasses import dataclass

from . import htypes


@dataclass(frozen=True, unsafe_hash=True)
class PythonModuleReq:

    code_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.code_name)

    @property
    def piece(self):
        return htypes.python_module_resource_target.python_module_req(self.code_name)

    def get_target(self, target_factory):
        return target_factory.python_module_resource(self.code_name)


class PythonModuleResourceTarget:

    def __init__(self, python_module_src):
        self._python_module_src = python_module_src
        self._completed = False

    @property
    def name(self):
        return f'resource/{self._python_module_src.name}'

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed
