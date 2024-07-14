import asyncio
import inspect
import logging
import traceback

from hyperapp.common.util import flatten, merge_dicts
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
from .code.requirement_factory import RequirementFactory
from .code.job_result import JobResult

log  = logging.getLogger(__name__)


class TestResultBase(JobResult):

    @staticmethod
    def _resolve_reqirement_refs(requirement_refs):
        return [
            rc_requirement_creg.invite(ref)
            for ref in requirement_refs
            ]

    @staticmethod
    def _used_imports_to_dict(used_imports_list):
        result = {}
        for rec in used_imports_list:
            result[rec.module_name] = rec.imports
        return result

    def __init__(self, status, used_imports, requirements, error=None, traceback=None):
        super().__init__(status, error, traceback)
        self._used_imports = used_imports
        self._requirements = requirements

    def _resolve_requirements(self, target_factory):
        req_to_target = {}
        for req in self._requirements:
            target = req.get_target(target_factory)
            req_to_target[req] = target
        return req_to_target

    def _update_tested_imports(self, target_factory):
        for module_name, import_list in self._used_imports.items():
            resource_tgt = target_factory.python_module_resource_by_module_name(module_name)
            resource_tgt.add_used_imports(import_list)


class SucceededTestResult(TestResultBase):

    @classmethod
    def from_piece(cls, piece):
        used_imports = cls._used_imports_to_dict(piece.used_imports)
        requirements = cls._resolve_reqirement_refs(piece.requirements)
        return cls(used_imports, requirements)

    def __init__(self, used_imports, requirements):
        super().__init__(JobStatus.ok, used_imports, requirements)

    def update_targets(self, my_target, target_set):
        self._update_tested_imports(target_set.factory)
        req_to_target = self._resolve_requirements(target_set.factory)
        my_target.set_alias_completed(req_to_target)


class IncompleteTestResult(TestResultBase):

    @classmethod
    def from_piece(cls, piece):
        used_imports = cls._used_imports_to_dict(piece.used_imports)
        requirements = cls._resolve_reqirement_refs(piece.requirements)
        return cls(used_imports, requirements, piece.error, piece.traceback)

    def __init__(self, used_imports, requirements, error, traceback):
        super().__init__(JobStatus.incomplete, used_imports, requirements, error, traceback)

    def update_targets(self, my_target, target_set):
        self._update_tested_imports(target_set.factory)
        req_to_target = self._resolve_requirements(target_set.factory)
        if req_to_target:  # TODO: remove after all requirement types are implemented.
            target_set.add(my_target.create_next_target(req_to_target))


class FailedTestResult(JobResult):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.error, piece.traceback)

    def __init__(self, requirements, error, traceback):
        super().__init__(JobStatus.failed, error, traceback)

    def update_targets(self, my_target, target_set):
        pass


class TestJob:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            resources=[rc_resource_creg.invite(d) for d in piece.resources],
            test_fn_name=piece.test_fn_name,
            )

    def __init__(self, python_module_src, idx, resources, test_fn_name):
        self._python_module_src = python_module_src
        self._idx = idx
        self._resources = resources
        self._test_fn_name = test_fn_name

    def __repr__(self):
        return f"<TestJob {self._python_module_src}/{self._test_fn_name}/{self._idx}>"

    @property
    def piece(self):
        return htypes.test_job.job(
            python_module=self._python_module_src.piece,
            idx=self._idx,
            resources=tuple(mosaic.put(d.piece) for d in self._resources),
            test_fn_name=self._test_fn_name,
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
            status, error_msg, traceback = self._prepare_import_error(x)
        else:
            test_fn = getattr(module, self._test_fn_name)
            try:
                value = test_fn()

                if inspect.isgenerator(value):
                    log.info("Expanding generator: %r", value)
                    value = list(value)

                if inspect.iscoroutine(value):
                    log.info("Running coroutine: %r", value)
                    value = asyncio.run(value)
            except Exception as x:
                status, error_msg, traceback = self._prepare_error(x, skip_entries=1)
        if status == JobStatus.failed:
            return htypes.test_job.failed_result(error_msg, tuple(traceback))
        req_set = self._imports_to_requirements(recorder.used_imports)
        req_refs = tuple(
            mosaic.put(req.piece)
            for req in req_set
            )
        if status == JobStatus.incomplete:
            return htypes.test_job.incomplete_result(
                used_imports=tuple(self._enum_used_imports(all_resources)),
                requirements=req_refs,
                error=error_msg,
                traceback=tuple(traceback),
                )
        return htypes.test_job.succeeded_result(
            used_imports=tuple(self._enum_used_imports(all_resources)),
            requirements=req_refs,
            )

    def _prepare_import_error(self, x):
        return self._prepare_error(x.original_error)

    def _prepare_error(self, x, skip_entries=0):
        traceback_entries = []
        cause = x
        while cause:
            traceback_entries += traceback.extract_tb(cause.__traceback__)
            cause = cause.__cause__
        for idx, entry in enumerate(traceback_entries):
            if entry.name == 'exec_module':
                del traceback_entries[:idx + 1]
                break
        else:
            del traceback_entries[:skip_entries]
        traceback_lines = traceback.format_list(traceback_entries)
        if isinstance(x, IncompleteImportedObjectError):
            return (JobStatus.incomplete, str(x), traceback_lines[:-1])
        else:
            return (JobStatus.failed, str(x), traceback_lines)

    def _imports_to_requirements(self, import_set):
        log.info("Used imports: %s", import_set)
        req_set = set()
        for import_path in import_set:
            req = RequirementFactory().requirement_from_import(import_path)
            if req:
                req_set.add(req)
        return req_set

    def _enum_used_imports(self, resources):
        recorder_dict = merge_dicts(d.recorders for d in resources)
        for module_name, recorder in recorder_dict.items():
            yield htypes.test_job.used_imports(
                module_name=module_name,
                imports=tuple(recorder.used_imports),
                )
