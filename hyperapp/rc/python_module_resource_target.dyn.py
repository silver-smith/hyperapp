import logging
import subprocess
from dataclasses import dataclass
from functools import cached_property

from hyperapp.common.util import flatten

from . import htypes
from .services import (
    hyperapp_dir,
    resource_module_factory,
    )
from .code.rc_requirement import Requirement
from .code.import_resource import ImportResource

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
        return ImportResource(['code', self.code_name], target.python_module_piece)


class PythonModuleResourceTarget:

    @classmethod
    def target_name_for_src(cls, python_module_src):
        return cls.target_name_for_module_name(python_module_src.name)

    @staticmethod
    def target_name_for_module_name(module_name):
        return f'resource/{module_name}'

    def __init__(self, python_module_src, custom_resource_registry):
        self._src = python_module_src
        self._custom_resource_registry = custom_resource_registry

    @property
    def name(self):
        return self.target_name_for_src(self._src)


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

    def __init__(self, python_module_src, custom_resource_registry, type_src_list, all_imports_known_tgt, import_alias_tgt):
        super().__init__(python_module_src, custom_resource_registry)
        self._type_src_list = type_src_list
        self._name_to_src = {
            (rec.module_name, rec.name): rec
            for rec in type_src_list
            }
        self._all_imports_known_tgt = all_imports_known_tgt
        self._import_alias_tgt = import_alias_tgt
        self._completed = False
        self._req_to_target = {}
        self._type_resources = []
        self._tests = set()

    def __repr__(self):
        return f"<CompiledPythonModuleResourceTarget {self.name}>"

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {self._all_imports_known_tgt, self._import_alias_tgt, *self._req_to_target.values(), *self._tests}

    def update_status(self):
        if self._completed:
            return
        if all(target.completed for target in self.deps):
            self._completed = True
            self._construct_res_module()

    def add_import_requirements(self, req_to_target):
        self._req_to_target = req_to_target

    def add_test_dep(self, test_target):
        self._tests.add(test_target)

    def add_used_imports(self, import_list):
        for name in import_list:
            if len(name) < 3:
                continue
            if name[0] != 'htypes':
                continue
            type_src = self._name_to_src[name[1:]]
            resource = ImportResource.from_type_src(type_src)
            self._type_resources.append(resource)

    @cached_property
    def python_module_piece(self):
        assert self._completed
        resources = list(filter(None, self._enum_resources()))  # TODO: Remove filter when all make_resource methods are implemented.
        import_list = flatten(d.import_records for d in resources)
        return self._src.python_module(import_list)

    def _enum_resources(self):
        yield from self._type_resources
        for req, target in self._req_to_target.items():
            yield req.make_resource(target)

    def _construct_res_module(self):
        rc_log.info("Construct: %s", self.name)
        python_module = self.python_module_piece
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
