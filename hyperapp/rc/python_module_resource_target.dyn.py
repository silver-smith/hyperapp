import logging
from dataclasses import dataclass

from . import htypes
from .code.requirement import Requirement

rc_log = logging.getLogger('rc')


@dataclass(frozen=True, unsafe_hash=True)
class PythonModuleReq(Requirement):

    code_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.code_name)

    @property
    def piece(self):
        return htypes.python_module_resource_target.python_module_req(self.code_name)

    def get_target(self, target_factory):
        return target_factory.python_module_resource_by_code_name(self.code_name)

    def make_resource(self, target):
        return None


class PythonModuleResourceTarget:

    @staticmethod
    def name_for_src(python_module_src):
        return f'resource/{python_module_src.name}'

    def __init__(self, python_module_src, all_imports_known_tgt, import_alias_tgt):
        self._python_module_src = python_module_src
        self._all_imports_known_tgt = all_imports_known_tgt
        self._import_alias_tgt = import_alias_tgt
        self._completed = False
        self._tests = set()

    def __repr__(self):
        return f"<PythonModuleResourceTarget {self.name}>"

    @property
    def name(self):
        return self.name_for_src(self._python_module_src)

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {self._all_imports_known_tgt, self._import_alias_tgt, *self._tests}

    def update_status(self):
        if self._completed:
            return
        if all(target.completed for target in self.deps):
            rc_log.info("Ready: %s", self.name)
            # self._completed = True

    def add_test_dep(self, test_target):
        self._tests.add(test_target)
