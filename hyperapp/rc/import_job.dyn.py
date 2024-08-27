import inspect
import traceback

from hyperapp.common.util import flatten
from hyperapp.resource.python_module import PythonModuleResourceImportError

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constants import JobStatus
from .code.build import PythonModuleSrc
from .code.builtin_resources import enum_builtin_resources
from .code.import_recorder import IncompleteImportedObjectError
from .code.requirement_factory import RequirementFactory
from .code.job_result import JobResult
from .code.system_job import SystemJob


class Function:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.name, piece.params)

    def __init__(self, name, params):
        self.name = name
        self.params = params


class ImportResultBase(JobResult):

    @staticmethod
    def _resolve_reqirement_refs(rc_requirement_creg, requirement_refs):
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
    def from_piece(cls, piece, rc_requirement_creg, rc_constructor_creg):
        requirements = cls._resolve_reqirement_refs(rc_requirement_creg, piece.requirements)
        functions = [
            Function.from_piece(fn)
            for fn in piece.functions
            ]
        constructors = [
            rc_constructor_creg.invite(ref)
            for ref in piece.constructors
            ]
        return cls(requirements, functions, constructors)

    def __init__(self, requirements, functions, constructors):
        super().__init__(JobStatus.ok, requirements)
        self._functions = functions
        self._constructors = constructors

    def update_targets(self, my_target, target_set):
        req_to_target = self._resolve_requirements(target_set.factory)
        if self._is_tests or self._is_fixtures:
            self._update_fixtures_targets(my_target, target_set)
        if self._is_tests:
            self._add_tests(my_target, target_set, req_to_target)
        elif not self._is_fixtures:
            self._update_resource(my_target, target_set, req_to_target)
        my_target.set_alias_requirements(req_to_target)
        target_set.update_deps_for(my_target.alias)

    def _update_fixtures_targets(self, my_target, target_set):
        import_alias_tgt = my_target.alias
        for ctr in self._constructors:
            ctr.update_fixtures_targets(import_alias_tgt, target_set)

    def _add_tests(self, my_target, target_set, req_to_target):
        for fn in self._functions:
            if not fn.name.startswith('test_'):
                continue
            test_alias, test_target = my_target.create_test_target(fn, req_to_target)
            target_set.add(test_alias)
            target_set.add(test_target)
            for req in self._requirements:
                req.update_tested_target(my_target, test_target, target_set)

    def _update_resource(self, my_target, target_set, req_to_target):
        resource_target = my_target.get_resource_target(target_set.factory)
        assert not resource_target.completed  # First tests import was incomplete? That is not yet supported.
        resource_target.add_import_requirements(req_to_target)
        target_set.update_deps_for(resource_target)
        for ctr in self._constructors:
            ctr.update_resource_targets(resource_target, target_set)

    @property
    def _is_tests(self):
        for req in self._requirements:
            if req.is_test_requirement:
                return True
        return False

    @property
    def _is_fixtures(self):
        for ctr in self._constructors:
            if ctr.is_fixture:
                return True
        return False


class IncompleteImportResult(ImportResultBase):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg):
        requirements = cls._resolve_reqirement_refs(rc_requirement_creg, piece.requirements)
        return cls(requirements, piece.error, piece.traceback)

    def __init__(self, requirements, error, traceback):
        super().__init__(JobStatus.incomplete, requirements, error, traceback)

    def update_targets(self, my_target, target_set):
        req_to_target = self._resolve_requirements(target_set.factory)
        target_set.add(my_target.create_next_target(req_to_target))


class FailedImportResult(JobResult):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.error, piece.traceback)

    def __init__(self, error, traceback):
        super().__init__(JobStatus.failed, error, traceback)

    def update_targets(self, my_target, target_set):
        pass


class ImportJob(SystemJob):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg, rc_resource_creg, system_config):
        return cls(
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            resources=[rc_resource_creg.invite(d) for d in piece.resources],
            cfg_item_creg=cfg_item_creg,
            system_config=system_config,
            )

    def __init__(self, python_module_src, idx, resources, cfg_item_creg=None, system_config=None):
        super().__init__(cfg_item_creg, system_config)
        self._src = python_module_src
        self._idx = idx
        self._resources = resources

    def __repr__(self):
        return f"<ImportJob {self._src}/{self._idx}>"

    @property
    def piece(self):
        return htypes.import_job.job(
            python_module=self._src.piece,
            idx=self._idx,
            resources=tuple(mosaic.put(d.piece) for d in self._resources),
            )

    def run(self):
        all_resources = [*enum_builtin_resources(), *self._resources]
        import_list = flatten(d.import_records for d in all_resources)
        recorder_piece, module_piece = self._src.recorded_python_module(import_list)
        recorder = pyobj_creg.animate(recorder_piece)
        system = self._prepare_system(all_resources)
        ctr_collector = system.resolve_service('ctr_collector')
        ctr_collector.set_wanted_import_piece(self._src.name, module_piece)
        ctr_collector.init_markers()
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
        constructors = tuple(self._enum_constructor_refs(system, ctr_collector))
        if status == JobStatus.ok:
            return htypes.import_job.succeeded_result(
                requirements=req_refs,
                functions=tuple(self._enum_functions(module)),
                constructors=constructors,
                )

    def _enum_functions(self, module):
        for name in dir(module):
            if name.startswith('_'):
                continue
            fn = getattr(module, name)
            if not callable(fn):
                continue
            if getattr(fn, '__module__', None) != module.__name__:
                continue  # Skip functions imported from other modules.
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
        error = f"{type(x).__name__}: {x}"
        if isinstance(x.original_error, IncompleteImportedObjectError):
            return (JobStatus.incomplete, error, traceback_lines[:-1])
        else:
            return (JobStatus.failed, error, traceback_lines)

    def _imports_to_requirements(self, import_set):
        # print("Used imports", import_set)
        req_set = set()
        for import_path in import_set:
            req = RequirementFactory().requirement_from_import(import_path)
            if req:
                req_set.add(req)
        return req_set
