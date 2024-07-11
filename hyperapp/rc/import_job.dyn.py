import inspect
import traceback

from hyperapp.common.util import flatten
from hyperapp.resource.python_module import PythonModuleResourceImportError

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    rc_requirement_creg,
    rc_resource_creg,
    )
from .code.rc_constants import JobStatus
from .code.build import PythonModuleSrc
from .code.builtin_resources import enum_builtin_resources
from .code.import_recorder import IncompleteImportedObjectError
from .code.requirement_factory import RequirementFactory
from .code.job_result import JobResult
from .code.test_requirement import TestedCodeReq, TestedServiceReq


class Function:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.name, piece.params)

    def __init__(self, name, params):
        self.name = name
        self.params = params


class ImportResultBase(JobResult):

    @staticmethod
    def _resolve_reqirement_refs(requirement_refs):
        return [
            rc_requirement_creg.invite(ref)
            for ref in requirement_refs
            ]

    def __init__(self, status, requirements, error=None, traceback=None):
        super().__init__(status, error, traceback)
        self._requirements = requirements

    def _resolve_requirements(self, target_factory):
        req_to_target = {}
        for req in self._requirements:
            target = req.get_target(target_factory)
            req_to_target[req] = target
        return req_to_target


class SucceededImportResult(ImportResultBase):

    @classmethod
    def from_piece(cls, piece):
        requirements = cls._resolve_reqirement_refs(piece.requirements)
        functions = [
            Function.from_piece(fn)
            for fn in piece.functions
            ]
        return cls(requirements, functions)

    def __init__(self, requirements, functions):
        super().__init__(JobStatus.ok, requirements)
        self._functions = functions

    def update_targets(self, import_target, target_set):
        req_to_target = self._resolve_requirements(target_set.factory)
        import_target.set_alias_completed(req_to_target)
        if not self._is_tests:
            return
        for fn in self._functions:
            if fn.name.startswith('test_'):
                test_target = import_target.create_test_target(fn, req_to_target)
                target_set.add(test_target)
                for req in self._requirements:
                    resource_target = req.get_tested_target(target_set.factory)
                    if resource_target:
                        resource_target.add_test_dep(test_target)

    @property
    def _is_tests(self):
        for req in self._requirements:
            if isinstance(req, (TestedServiceReq, TestedCodeReq)):
                return True
        return False


class IncompleteImportResult(ImportResultBase):

    @classmethod
    def from_piece(cls, piece):
        requirements = cls._resolve_reqirement_refs(piece.requirements)
        return cls(requirements, piece.error, piece.traceback)

    def __init__(self, requirements, error, traceback):
        super().__init__(JobStatus.incomplete, requirements, error, traceback)

    def update_targets(self, import_target, target_set):
        req_to_target = self._resolve_requirements(target_set.factory)
        if req_to_target:  # TODO: remove after all requirement types are implemented.
            target_set.add(import_target.create_next_target(req_to_target))


class FailedImportResult(JobResult):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.error, piece.traceback)

    def __init__(self, requirements, error, traceback):
        super().__init__(JobStatus.failed, error, traceback)

    def update_targets(self, import_target, target_set):
        pass


class ImportJob:

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
        return f"<ImportJob {self._python_module_src}/{self._idx}>"

    @property
    def piece(self):
        return htypes.import_job.job(
            python_module=self._python_module_src.piece,
            idx=self._idx,
            resources=tuple(mosaic.put(d.piece) for d in self._resources),
            )

    def run(self):
        all_resources = [*enum_builtin_resources(), *self._resources]
        import_list = flatten(d.import_records for d in all_resources)
        recorder_piece, module_piece = self._python_module_src.recorded_python_module(import_list)
        recorder = pyobj_creg.animate(recorder_piece)
        try:
            module = pyobj_creg.animate(module_piece)
            status = JobStatus.ok
        except PythonModuleResourceImportError as x:
            status, error_msg, traceback = self._prepare_error(x)
        if status == JobStatus.failed:
            return htypes.import_job.failed_result(error_msg, tuple(traceback))
        req_set = self._imports_to_requirements(recorder.used_imports)
        req_refs = tuple(
            mosaic.put(req.piece)
            for req in req_set
            )
        if status == JobStatus.incomplete:
            return htypes.import_job.incomplete_result(
                requirements=req_refs,
                error=error_msg,
                traceback=tuple(traceback),
                )
        if status == JobStatus.ok:
            return htypes.import_job.succeeded_result(
                requirements=req_refs,
                functions=tuple(self._enum_functions(module)),
                )

    def _enum_functions(self, module):
        for name in dir(module):
            if name.startswith('_'):
                continue
            fn = getattr(module, name)
            if not callable(fn):
                continue
            try:
                signature = inspect.signature(fn)
            except ValueError as x:
                if 'no signature found for builtin type' in str(x):
                    continue
                raise
            yield htypes.import_job.function(
                name=name,
                params=tuple(signature.parameters.keys()),
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
