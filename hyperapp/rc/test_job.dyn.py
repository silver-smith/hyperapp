import inspect
import logging
from collections import defaultdict
from functools import cached_property

from hyperapp.common.util import flatten, merge_dicts
from hyperapp.common.config_item_missing import ConfigItemMissingError

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
from .code.job_result import JobResult
from .code.system import UnknownServiceError
from .code.system_probe import SystemProbe
from .code.fixture_probe import FixtureProbeTemplate
from .code.system_job import Result, SystemJob

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
        raise htypes.rc_job.unknown_service_error(x.service_name) from x
    except ConfigItemMissingError as x:
        # Assume we get only type-keyed errors.
        # If not, we may add special checks for primitive types like str.
        t_ref = pyobj_creg.actor_to_ref(x.key)
        raise htypes.rc_job.config_item_missing_error(x.service_name, t_ref) from x
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


class _TestJobResult(Result):

    @staticmethod
    def _enum_used_imports(resources):
        recorder_dict = merge_dicts(d.recorders for d in resources)
        for module_name, recorder in recorder_dict.items():
            yield htypes.test_job.used_imports(
                module_name=module_name,
                imports=tuple(recorder.used_imports),
                )

    def _used_imports(self, resources):
        return tuple(self._enum_used_imports(resources))


class _TestJobError(Exception, _TestJobResult):

    def __init__(self, error_msg=None, traceback=None, missing_reqs=None):
        Exception.__init__(self, error_msg)
        _TestJobResult.__init__(self, error_msg, traceback, missing_reqs)


class _FailedError(_TestJobError):

    def make_result_piece(self, resources, recorder, system):
        return htypes.test_job.failed_result(
            used_requirements=self._used_requirement_refs(system),
            error=self.error_msg,
            traceback=tuple(self.traceback),
            )


class _IncompleteError(_TestJobError):

    def make_result_piece(self, resources, recorder, system):
        return htypes.test_job.incomplete_result(
            missing_requirements=self._missing_requirement_refs(recorder),
            used_requirements=self._used_requirement_refs(system),
            used_imports=self._used_imports(resources),
            error=self._error_msg,
            traceback=tuple(self._traceback),
            )


class _Succeeded(_TestJobResult):

    def make_result_piece(self, resources, recorder, system):
        return htypes.test_job.succeeded_result(
            used_requirements=self._used_requirement_refs(system),
            used_imports=self._used_imports(resources),
            constructors=self._constructor_refs(system),
            )


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
        resources = [*enum_builtin_resources(), *self._resources]
        import_list = flatten(d.import_records for d in resources)
        recorder_piece, module_piece = self._src.recorded_python_module(import_list)
        recorder = pyobj_creg.animate(recorder_piece)
        ctr_collector = None
        try:
            system = self.convert_errors(self._unsafe_run, resources, module_piece)
        except _TestJobError as x:
            result = x
            system = None
        else:
            result = _Succeeded()
        return result.make_result_piece(resources, recorder, system)

    def _unsafe_run(self, resources, module_piece):
        system = self._prepare_system(resources)
        ctr_collector = system['ctr_collector']
        ctr_collector.ignore_module(module_piece)
        module = pyobj_creg.animate(module_piece)
        root_probe = self._make_root_fixture(system, module_piece, module)
        system.update_config('system', {self._root_name: root_probe})
        self._run_system(system)
        return system

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
        rpc_service_wrapper = system['rpc_service_wrapper']
        subprocess_rpc_main = system['subprocess_rpc_main']
        rpc_servant_wrapper.set(self._wrap_rpc_servant)
        rpc_service_wrapper.set(self._wrap_rpc_service)
        subprocess_rpc_main.set(test_subprocess_rpc_main)
        try:
            return system.run(self._root_name)
        finally:
            subprocess_rpc_main.reset()
            rpc_service_wrapper.reset()
            rpc_servant_wrapper.reset()

    def incomplete_error(self, error_msg, traceback=None, missing_reqs=None):
        raise _IncompleteError(error_msg, traceback[:-1] if traceback else None, missing_reqs)

    def failed_error(self, error_msg, traceback):
        raise _FailedError(error_msg, traceback)

    def _wrap_rpc_servant(self, servant_ref, kw):
        wrapped_servant_ref = pyobj_creg.actor_to_ref(rpc_servant_wrapper)
        wrapped_kw = {'_real_servant_ref': servant_ref, **kw}
        return (wrapped_servant_ref, wrapped_kw)

    def _wrap_rpc_service(self, service_name, kw):
        wrapped_kw = {'_real_service_name': service_name, **kw}
        return ('test_job_rpc_service_wrapper', wrapped_kw)
