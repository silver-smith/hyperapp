import inspect
import logging
import traceback
from collections import defaultdict
from functools import cached_property

from hyperapp.common.htypes import HException
from hyperapp.common.util import flatten, merge_dicts
from hyperapp.common.config_item_missing import ConfigItemMissingError
from hyperapp.resource.python_module import PythonModuleResourceImportError

from . import htypes
from .services import (
    mosaic,
    hyperapp_dir,
    pyobj_creg,
    )
from .code.config_ctl import DictConfigCtl
from .code.rc_constants import JobStatus
from .code.build import PythonModuleSrc
from .code.builtin_resources import enum_builtin_resources
from .code.import_recorder import IncompleteImportedObjectError
from .code.requirement_factory import RequirementFactory
from .code.job_result import JobResult
from .code.service_req import ServiceReq
from .code.actor_req import ActorReq
from .code.system import UnknownServiceError
from .code.system_probe import SystemProbe
from .code.fixture_probe import FixtureProbeTemplate
from .code.system_job import SystemJob

log  = logging.getLogger(__name__)
rc_log = logging.getLogger('rc')


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

    @property
    def _reqs_desc(self):
        return ", ".join(r.desc for r in self._requirements if r.desc)

    @property
    def desc(self):
        return super().desc + f", needs {self._reqs_desc}"

    def update_targets(self, my_target, target_set):
        self._update_tested_imports(target_set.factory)
        req_to_target = self._resolve_requirements(target_set.factory)
        if set(req_to_target) <= my_target.req_set:
            # No new requirements are discovered.
            rc_log.error("%s: Infinite loop detected with: %s", my_target.name, self._reqs_desc)
        else:
            target_set.add(my_target.create_next_target(req_to_target))


class FailedTestResult(JobResult):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.error, piece.traceback)

    def __init__(self, error, traceback):
        super().__init__(JobStatus.failed, error, traceback)

    def update_targets(self, my_target, target_set):
        pass


def _catch_errors(fn, **kw):
    try:
        return fn(**kw)
    except UnknownServiceError as x:
        raise htypes.test_job.unknown_service_error(x.service_name) from x
    except ConfigItemMissingError as x:
        # Assume we get only type-keyed errors.
        # If not, we may add special checks for primitive types like str.
        t_ref = pyobj_creg.actor_to_ref(x.key)
        raise htypes.test_job.config_item_missing_error(x.service_name, t_ref) from x
    except Exception as x:
        raise RuntimeError(f"In test servant {servant}: {x}") from x


def rpc_servant_wrapper(_real_servant_ref, **kw):
    servant = pyobj_creg.invite(_real_servant_ref)
    return _catch_errors(servant, **kw)


def rpc_service_wrapper(system, _real_service_name, **kw):
    def run():
        service = system.resolve_service(_real_service_name)
        return service(**kw)
    return _catch_errors(run)


def test_subprocess_rpc_main(connection, received_refs, system_config_piece, root_name, **kw):
    system = SystemProbe()
    system.load_config(system_config_piece)
    _ = system.resolve_service('marker_registry')  # Init markers.
    system.run(root_name, connection, received_refs, **kw)

        
class TestJob(SystemJob):

    @classmethod
    def from_piece(cls, piece, rc_resource_creg, system_config_piece):
        return cls(
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            resources=[rc_resource_creg.invite(d) for d in piece.resources],
            test_fn_name=piece.test_fn_name,
            system_config_piece=system_config_piece,
            )

    def __init__(self, python_module_src, idx, resources, test_fn_name, system_config_piece=None):
        super().__init__(system_config_piece)
        self._src = python_module_src
        self._idx = idx
        self._resources = resources
        self._test_fn_name = test_fn_name

    def __repr__(self):
        return f"<TestJob {self._src}/{self._test_fn_name}/{self._idx}>"

    @cached_property
    def piece(self):
        resource_refs = sorted(mosaic.put(r.piece) for r in self._resources)
        return htypes.test_job.job(
            python_module=self._src.piece,
            idx=self._idx,
            resources=tuple(resource_refs),
            test_fn_name=self._test_fn_name,
            )

    def run(self):
        all_resources = [*enum_builtin_resources(), *self._resources]
        import_list = flatten(d.import_records for d in all_resources)
        recorder_piece, module_piece = self._src.recorded_python_module(import_list)
        recorder = pyobj_creg.animate(recorder_piece)
        try:
            system = self._prepare_system(all_resources)
        except PythonModuleResourceImportError as x:
            status, error_msg, traceback = self._prepare_import_error(x)
        except UnknownServiceError as x:
            status = JobStatus.incomplete
            error_msg = f"{type(x).__name__}: {x}"
            traceback = []
            req_set = {ServiceReq(x.service_name)}
        except ConfigItemMissingError as x:
            status = JobStatus.incomplete
            error_msg = f"{type(x).__name__}: {x}"
            traceback = []
            req_set = {ActorReq(x.service_name, x.key)}
        else:
            ctr_collector = system.resolve_service('ctr_collector')
            ctr_collector.ignore_module(module_piece)
            status, error_msg, traceback, module = self._import_module(module_piece)
            if status == JobStatus.ok:
                root_probe = self._make_root_fixture(system, module_piece, module)
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
        constructors = tuple(self._enum_constructor_refs(ctr_collector))
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

    def _make_root_fixture(self, system, module_piece, module):
        ctl = DictConfigCtl(system['cfg_item_creg'])
        ctl_ref = mosaic.put(ctl.piece)
        test_fn = getattr(module, self._test_fn_name)
        params = tuple(inspect.signature(test_fn).parameters)
        test_fn_piece = htypes.builtin.attribute(
            object=mosaic.put(module_piece),
            attr_name=self._test_fn_name,
            )
        return FixtureProbeTemplate(self._test_fn_name, ctl_ref, test_fn_piece, params)

    def _run_system(self, system):
        rpc_servant_wrapper = system['rpc_servant_wrapper']
        rpc_servant_wrapper.set(self._wrap_rpc_servant)
        rpc_service_wrapper = system['rpc_service_wrapper']
        rpc_service_wrapper.set(self._wrap_rpc_service)
        subprocess_rpc_main = system['subprocess_rpc_main']
        subprocess_rpc_main.set(test_subprocess_rpc_main)
        
        try:
            system.run(self._root_name)
            status = JobStatus.ok
            error_msg = traceback = None
        except HException as x:
            if isinstance(x, htypes.test_job.unknown_service_error):
                req = ServiceReq(x.service_name)
                error = f"{type(x).__name__}: {x}"
                return (JobStatus.incomplete, error, [], {req})
            if isinstance(x, htypes.test_job.config_item_missing_error):
                key = pyobj_creg.invite(x.t)
                req = ActorReq(x.service_name, key)
                error = f"{type(x).__name__}: {x}"
                return (JobStatus.incomplete, error, [], {req})
            raise
        except UnknownServiceError as x:
            req = ServiceReq(x.service_name)
            error = f"{type(x).__name__}: {x}"
            return (JobStatus.incomplete, error, [], {req})
        except ConfigItemMissingError as x:
            req = ActorReq(x.service_name, x.key)
            error = f"{type(x).__name__}: {x}"
            return (JobStatus.incomplete, error, [], {req})
        except IncompleteImportedObjectError as x:
            if list(x.path[:1]) == ['htypes']:
                status = JobStatus.failed
                path = '.'.join(x.path)
                error_msg = f"Unknown type: {path}" 
                traceback = self._prepare_traceback(x)[:-1]
            else:
                status, error_msg, traceback = self._prepare_error(x)
        except BaseException as x:
            status, error_msg, traceback = self._prepare_error(x)
        finally:
            subprocess_rpc_main.reset()
            rpc_servant_wrapper.reset()
            rpc_service_wrapper.reset()
        return (status, error_msg, traceback, set())

    def _prepare_import_error(self, x):
        return self._prepare_error(x.original_error)

    def _prepare_traceback(self, x):
        traceback_entries = []
        cause = x
        while cause:
            traceback_entries += traceback.extract_tb(cause.__traceback__)
            last_cause = cause
            cause = cause.__cause__
        for idx, entry in enumerate(traceback_entries):
            if entry.name == 'exec_module':
                del traceback_entries[:idx + 1]
                break
        for idx, entry in enumerate(traceback_entries):
            fpath = entry.filename.split('/')[-2:]
            fname = '/'.join(fpath).replace('.dyn.py', '')
            if fname not in {'rc/test_job', 'system/system', 'rc/system_probe', 'rc/fixture_probe'}:
                del traceback_entries[:idx]
                break
        line_list = traceback.format_list(traceback_entries)
        if isinstance(last_cause, htypes.rpc.server_error):
            for entry in last_cause.traceback:
                line_list += [line + '\n' for line in entry.splitlines()]
        return line_list

    def _prepare_error(self, x):
        traceback_lines = self._prepare_traceback(x)
        if isinstance(x, htypes.rpc.server_error):
            message = x.message
        else:
            message = str(x)
        error = f"{type(x).__name__}: {message}"
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

    def _wrap_rpc_servant(self, servant_ref, kw):
        wrapped_servant_ref = pyobj_creg.actor_to_ref(rpc_servant_wrapper)
        wrapped_kw = {'_real_servant_ref': servant_ref, **kw}
        return (wrapped_servant_ref, wrapped_kw)

    def _wrap_rpc_service(self, service_name, kw):
        wrapped_kw = {'_real_service_name': service_name, **kw}
        return ('test_job_rpc_service_wrapper', wrapped_kw)
