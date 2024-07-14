import logging
import subprocess
from dataclasses import dataclass

from hyperapp.common.util import flatten

from . import htypes
from .services import (
    hyperapp_dir,
    resource_module_factory,
    )
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

    def __init__(self, python_module_src, custom_resource_registry):
        self._src = python_module_src
        self._custom_resource_registry = custom_resource_registry

    @property
    def name(self):
        return self.name_for_src(self._src)


class ManualPythonModuleResourceTarget(PythonModuleResourceTarget):

    def __repr__(self):
        return f"<ManualPythonModuleResourceTarget {self.name}>"

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return True

    @property
    def deps(self):
        return set()

    def update_status(self):
        pass


class CompiledPythonModuleResourceTarget(PythonModuleResourceTarget):

    def __init__(self, python_module_src, custom_resource_registry, all_imports_known_tgt, import_alias_tgt):
        super().__init__(python_module_src, custom_resource_registry)
        self._all_imports_known_tgt = all_imports_known_tgt
        self._import_alias_tgt = import_alias_tgt
        self._completed = False
        self._req_to_target = {}
        self._tests = set()

    def __repr__(self):
        return f"<CompiledPythonModuleResourceTarget {self.name}>"

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return False
        # return self._completed

    @property
    def deps(self):
        return {self._all_imports_known_tgt, self._import_alias_tgt, *self._req_to_target.values(), *self._tests}

    def update_status(self):
        if self._completed:
            return
        if all(target.completed for target in self.deps):
            self._construct_res_module()
            self._completed = True

    def add_import_requirements(self, req_to_target):
        self._req_to_target = req_to_target

    def add_test_dep(self, test_target):
        self._tests.add(test_target)

    def _enum_resources(self):
        for req, target in self._req_to_target.items():
            yield req.make_resource(target)

    def _construct_res_module(self):
        rc_log.info("Construct: %s", self.name)
        resources = list(filter(None, self._enum_resources()))  # TODO: Remove filter when all make_resource methods are implemented.
        import_list = flatten(d.import_records for d in resources)
        python_module = self._src.python_module(import_list)
        resource_module = resource_module_factory(self._custom_resource_registry, self._src.name)
        resource_module[f'{self._src.stem}.module'] = python_module
        text = resource_module.as_text
        res_path = hyperapp_dir / self._src.resource_path
        p = subprocess.run(
            ['diff', '-u', str(res_path), '-'],
            input=text.encode(),
            stdout=subprocess.PIPE,
            )
        if p.returncode == 0:
            rc_log.info("No diffs")
        else:
            rc_log.info("Diff:\n%s", p.stdout.decode())
