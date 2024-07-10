import inspect
import traceback

from hyperapp.common.util import flatten
from hyperapp.resource.python_module import PythonModuleResourceImportError

from . import htypes
from .services import (
    mosaic,
    hyperapp_dir,
    pyobj_creg,
    rc_requirement_creg,
    rc_resource_creg,
    )
from .code.rc_constants import JobStatus
from .code.build import PythonModuleSrc
from .code.builtin_resources import enum_builtin_resources
from .code.import_recorder import IncompleteImportedObjectError
# from .code.requirement_factory import RequirementFactory
from .code.job_result import JobResult


class SucceededTestResult(JobResult):

    @classmethod
    def from_piece(cls, piece):
        requirements = cls._resolve_reqirement_refs(piece.requirements)
        return cls(requirements)

    @staticmethod
    def _resolve_reqirement_refs(requirement_refs):
        return [
            rc_requirement_creg.invite(ref)
            for ref in requirement_refs
            ]

    def __init__(self, requirements):
        super().__init__(JobStatus.ok, requirements)

    def update_targets(self, import_target, target_set):
        pass


class TestJob:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            resources=[rc_resource_creg.invite(d) for d in piece.resources],
            )

    def __init__(self, python_module_src, idx, resources):
        self._python_module_src = python_module_src
        self._idx = idx
        self._resources = resources

    def __repr__(self):
        return f"<TestJob {self._python_module_src}/{self._idx}>"

    @property
    def piece(self):
        return htypes.test_job.job(
            python_module=self._python_module_src.piece,
            idx=self._idx,
            resources=tuple(mosaic.put(d.piece) for d in self._resources),
            )

    def run(self):
        src = self._python_module_src
        all_resources = [*enum_builtin_resources(), *self._resources]
        return htypes.test_job.succeeded_result(
            requirements=(),
            )

    def _prepare_error(self, x):
        traceback_entries = []
        cause = x.original_error
        while cause:
            traceback_entries += traceback.extract_tb(cause.__traceback__)
            cause = cause.__cause__
        for idx, entry in enumerate(traceback_entries):
            if entry.name == 'exec_module':
                del traceback_entries[:idx + 1]
                break
        traceback_lines = traceback.format_list(traceback_entries)
        if isinstance(x.original_error, IncompleteImportedObjectError):
            return (JobStatus.incomplete, str(x), traceback_lines[:-1])
        else:
            return (JobStatus.failed, str(x), traceback_lines)

    def _imports_to_requirements(self, import_set):
        # print("Used imports", import_set)
        req_set = set()
        for import_path in import_set:
            req = RequirementFactory().requirement_from_import(import_path)
            if req:
                req_set.add(req)
        return req_set
