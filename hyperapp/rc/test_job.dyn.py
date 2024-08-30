import inspect
import logging
import traceback
from collections import defaultdict

from hyperapp.common.util import flatten, merge_dicts
from hyperapp.resource.python_module import PythonModuleResourceImportError

from . import htypes
from .services import (
    mosaic,
    hyperapp_dir,
    pyobj_creg,
    )
from .code.rc_constants import JobStatus
from .code.build import PythonModuleSrc
from .code.builtin_resources import enum_builtin_resources
from .code.import_recorder import IncompleteImportedObjectError
from .code.requirement_factory import RequirementFactory
from .code.job_result import JobResult
from .code.service_resource import ServiceReq
from .code.actor_resource import ActorReq
from .code.system import UnknownServiceError, NotATemplate
from .code.system_probe import ConfigItemRequiredError, FixtureProbeTemplate
from .code.system_job import SystemJob

log  = logging.getLogger(__name__)


class TestResultBase(JobResult):

    @staticmethod
    def _resolve_reqirement_refs(rc_requirement_creg, requirement_refs):
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
    def from_piece(cls, piece, rc_requirement_creg, rc_constructor_creg):
        used_imports = cls._used_imports_to_dict(piece.used_imports)
        requirements = cls._resolve_reqirement_refs(rc_requirement_creg, piece.requirements)
        constructors = [
            rc_constructor_creg.invite(ref)
            for ref in piece.constructors
            ]
        return cls(used_imports, requirements, constructors)

    def __init__(self, used_imports, requirements, constructors):
        super().__init__(JobStatus.ok, used_imports, requirements)
        self._constructors = constructors

    def update_targets(self, my_target, target_set):
        req_to_target = self._resolve_requirements(target_set.factory)
        self._update_tested_imports(target_set.factory)
        self._update_ctr_targets(target_set)
        my_target.set_alias_completed(req_to_target)

    def _update_ctr_targets(self, target_set):
        for ctr in self._constructors:
            ctr.update_targets(target_set)


class IncompleteTestResult(TestResultBase):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg):
        used_imports = cls._used_imports_to_dict(piece.used_imports)
        requirements = cls._resolve_reqirement_refs(rc_requirement_creg, piece.requirements)
        return cls(used_imports, requirements, piece.error, piece.traceback)

    def __init__(self, used_imports, requirements, error, traceback):
        super().__init__(JobStatus.incomplete, used_imports, requirements, error, traceback)

    def update_targets(self, my_target, target_set):
        self._update_tested_imports(target_set.factory)
        req_to_target = self._resolve_requirements(target_set.factory)
        target_set.add(my_target.create_next_target(req_to_target))


class FailedTestResult(JobResult):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.error, piece.traceback)

    def __init__(self, error, traceback):
        super().__init__(JobStatus.failed, error, traceback)

    def update_targets(self, my_target, target_set):
        pass


class TestJob(SystemJob):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg, rc_resource_creg, system_config):
        return cls(
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            resources=[rc_resource_creg.invite(d) for d in piece.resources],
            test_fn_name=piece.test_fn_name,
            cfg_item_creg=cfg_item_creg,
            system_config=system_config,
            )

    def __init__(self, python_module_src, idx, resources, test_fn_name, cfg_item_creg=None, system_config=None):
        super().__init__(cfg_item_creg, system_config)
        self._src = python_module_src
        self._idx = idx
        self._resources = resources
        self._test_fn_name = test_fn_name

    def __repr__(self):
        return f"<TestJob {self._src}/{self._test_fn_name}/{self._idx}>"

    @property
    def piece(self):
        return htypes.test_job.job(
            python_module=self._src.piece,
            idx=self._idx,
            resources=tuple(mosaic.put(d.piece) for d in self._resources),
            test_fn_name=self._test_fn_name,
            )

    def run(self):
        all_resources = [*enum_builtin_resources(), *self._resources]
        import_list = flatten(d.import_records for d in all_resources)
        recorder_piece, module_piece = self._src.recorded_python_module(import_list)
        recorder = pyobj_creg.animate(recorder_piece)
        system = self._prepare_system(all_resources)
        ctr_collector = system.resolve_service('ctr_collector')
        ctr_collector.ignore_module(module_piece)
        ctr_collector.init_markers()
        status, error_msg, traceback, module = self._import_module(module_piece)
        if status == JobStatus.ok:
            root_probe = self._make_root_fixture(module)
            system.update_config('system', {self._root_name: root_probe})
            status, error_msg, traceback, req_set = self._run_system(system)
        else:
            req_set = set()
        if status == JobStatus.failed:
            return htypes.test_job.failed_result(error_msg, tuple(traceback))
        req_set |= self._imports_to_requirements(recorder.used_imports)
        req_refs = tuple(
            mosaic.put(req.piece)
            for req in req_set
            )
        used_imports = tuple(self._enum_used_imports(all_resources))
        if status == JobStatus.incomplete:
            return htypes.test_job.incomplete_result(
                used_imports=used_imports,
                requirements=req_refs,
                error=error_msg,
                traceback=tuple(traceback),
                )
        constructors = tuple(self._enum_constructor_refs(system, ctr_collector))
        return htypes.test_job.succeeded_result(
            used_imports=used_imports,
            requirements=req_refs,
            constructors=constructors,
            )

    def _import_module(self, module_piece):
        try:
            module = pyobj_creg.animate(module_piece)
            status = JobStatus.ok
            error_msg = traceback = None
        except PythonModuleResourceImportError as x:
            status, error_msg, traceback = self._prepare_import_error(x)
            module = None
        return (status, error_msg, traceback, module)

    @property
    def _root_name(self):
        return self._test_fn_name

    def _make_root_fixture(self, module):
        test_fn = getattr(module, self._test_fn_name)
        params = tuple(inspect.signature(test_fn).parameters)
        return FixtureProbeTemplate(test_fn, params)

    def _run_system(self, system):
        try:
            system.run(self._root_name)
            status = JobStatus.ok
            error_msg = traceback = None
        except UnknownServiceError as x:
            req = ServiceReq(x.service_name, self._cfg_item_creg)
            error = f"{type(x).__name__}: {x}"
            return (JobStatus.incomplete, error, [], {req})
        except ConfigItemRequiredError as x:
            req = ActorReq(self._cfg_item_creg, x.service_name, x.key)
            error = f"{type(x).__name__}: {x}"
            return (JobStatus.incomplete, error, [], {req})
        except IncompleteImportedObjectError as x:
            if list(x.path[:1]) == ['htypes']:
                status = JobStatus.failed
                path = '.'.join(x.path)
                error_msg = f"Unknown type: {path}" 
                traceback = self._prepare_traceback(x)[:-1]
            else:
                status, error_msg, traceback = self._prepare_error(x, skip_entries=1)
        except Exception as x:
            status, error_msg, traceback = self._prepare_error(x, skip_entries=1)
        return (status, error_msg, traceback, set())

    def _prepare_import_error(self, x):
        return self._prepare_error(x.original_error)

    def _prepare_traceback(self, x, skip_entries=0):
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
        return traceback.format_list(traceback_entries)

    def _prepare_error(self, x, skip_entries=0):
        traceback_lines = self._prepare_traceback(x, skip_entries)
        error = f"{type(x).__name__}: {x}"
        if isinstance(x, IncompleteImportedObjectError):
            return (JobStatus.incomplete, error, traceback_lines[:-1])
        else:
            return (JobStatus.failed, error, traceback_lines)

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
