import inspect
import traceback
from functools import cached_property

from hyperapp.common.util import flatten

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constants import JobStatus
from .code.build import PythonModuleSrc
from .code.builtin_resources import enum_builtin_resources
from .code.config_item_resource import ConfigItemResource
from .code.job_result import JobResult
from .code.system_job import Result, SystemJob, SystemJobResult
from .code.test_module_resources_req import TestModuleResourcesReq


class Function:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.name, piece.params)

    def __init__(self, name, params):
        self.name = name
        self.params = params

    @property
    def piece(self):
        return htypes.import_job.function(self.name, tuple(self.params))


class _SucceededImportResultBase(SystemJobResult):

    def __init__(self, status, used_reqs, all_reqs, error=None, traceback=None):
        super().__init__(status, used_reqs, error, traceback)
        self._all_reqs = all_reqs

    def _add_tests_import(self, import_tgt, target_set):
        for req in self._all_reqs:
            req.apply_tests_import(import_tgt, target_set)

    @property
    def _is_tests(self):
        for req in self._all_reqs:
            if req.is_test_requirement:
                return True
        return False


class SucceededImportResult(_SucceededImportResultBase):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg, rc_constructor_creg):
        used_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.used_requirements)
        all_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.all_requirements)
        functions = [
            Function.from_piece(fn)
            for fn in piece.functions
            ]
        constructors = [
            rc_constructor_creg.invite(ref)
            for ref in piece.constructors
            ]
        return cls(used_reqs, all_reqs, functions, constructors)

    def __init__(self, used_reqs, all_reqs, functions, constructors):
        super().__init__(JobStatus.ok, used_reqs, all_reqs)
        self._functions = functions
        self._constructors = constructors

    @property
    def piece(self):
        return htypes.import_job.succeeded_result(
            used_requirements=tuple(mosaic.put(req.piece) for req in self._used_reqs),
            all_requirements=tuple(mosaic.put(req.piece) for req in self._all_reqs),
            functions=tuple(f.piece for f in self._functions),
            constructors=tuple(mosaic.put(ctr.piece) for ctr in self._constructors),
            )

    def cache_target_name(self, my_target):
        return my_target.import_tgt.name

    @property
    def used_reqs(self):
        return self._used_reqs

    # Called for cached result before used requirements are ready.
    def non_ready_update_targets(self, import_tgt, target_set):
        if self._is_tests:
            self._add_tests_import(import_tgt, target_set)

    def update_targets(self, import_tgt, target_set):
        req_to_target = self._resolve_requirements(target_set.factory, self._all_reqs)
        if self._is_tests or self._is_fixtures:
            self._update_fixtures_targets(import_tgt, target_set)
        if self._is_tests:
            self._add_tests_import(import_tgt, target_set)
            self._add_tests(import_tgt, target_set, req_to_target)
        elif not self._is_fixtures:
            self._update_resource(import_tgt, target_set, req_to_target)
        import_tgt.set_requirements(req_to_target)

    def _update_fixtures_targets(self, import_tgt, target_set):
        for ctr in self._constructors:
            ctr.update_fixtures_targets(import_tgt, target_set)

    def _add_tests(self, import_tgt, target_set, req_to_target):
        import_req = TestModuleResourcesReq(import_tgt.module_name)
        req_to_target = {
            **req_to_target,
            import_req: import_req.get_target(target_set.factory),
            }
        for fn in self._functions:
            if not fn.name.startswith('test_'):
                continue
            import_tgt.create_test_target(fn, req_to_target)

    def _update_resource(self, import_tgt, target_set, req_to_target):
        resource_target = import_tgt.get_resource_target(target_set.factory)
        assert not resource_target.completed  # First tests import was incomplete? That is not yet supported.
        resource_target.add_import_requirements(req_to_target)
        for ctr in self._constructors:
            ctr.update_resource_targets(resource_target, target_set)

    @property
    def _is_fixtures(self):
        for ctr in self._constructors:
            if ctr.is_fixture:
                return True
        return False


class IncompleteImportResult(_SucceededImportResultBase):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg):
        missing_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.missing_requirements)
        all_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.all_requirements)
        return cls(missing_reqs, all_reqs, piece.error, piece.traceback)

    def __init__(self, missing_reqs, all_reqs, error, traceback):
        super().__init__(JobStatus.incomplete, set(), all_reqs, error, traceback)
        self._missing_reqs = missing_reqs

    @property
    def piece(self):
        return htypes.import_job.incomplete_result(
            missing_requirements=tuple(mosaic.put(req.piece) for req in self._missing_reqs),
            all_requirements=tuple(mosaic.put(req.piece) for req in self._all_reqs),
            error=self.error,
            traceback=tuple(self.traceback),
            )

    @property
    def _reqs_desc(self):
        return ", ".join(r.desc for r in self._missing_reqs if r.desc)

    @property
    def desc(self):
        return super().desc + f", needs {self._reqs_desc}"

    def update_targets(self, import_tgt, target_set):
        if self._is_tests:
            self._add_tests_import(import_tgt, target_set)
        req_to_target = self._resolve_requirements(target_set.factory, self._missing_reqs)
        target_set.add(import_tgt.create_next_job_target(req_to_target))


class FailedImportResult(SystemJobResult):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg):
        used_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.used_requirements)
        return cls(used_reqs, piece.error, piece.traceback)

    def __init__(self, used_reqs, error, traceback):
        super().__init__(JobStatus.failed, used_reqs, error, traceback)

    @property
    def piece(self):
        return htypes.import_job.failed_result(
            used_requirements=tuple(mosaic.put(req.piece) for req in self._used_reqs),
            error=self.error,
            traceback=tuple(self.traceback),
            )

    def update_targets(self, import_tgt, target_set):
        pass


class _ImportJobResult(Result):
    pass


class _Succeeded(_ImportJobResult):

    @staticmethod
    def _enum_functions(module):
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
            yield Function(name, params=list(signature.parameters.keys()),)

    def make_result(self, recorder, module, key_to_req, system):
        system_reqs = self._used_system_reqs(key_to_req, system)
        missing_import_reqs = self._imports_to_requirements(recorder.missing_imports)
        used_import_reqs = self._imports_to_requirements(recorder.used_imports)
        return SucceededImportResult(
            used_reqs=set(req for req in system_reqs | used_import_reqs if not req.is_builtin),
            all_reqs=system_reqs | missing_import_reqs | used_import_reqs,
            functions=list(self._enum_functions(module)),
            constructors=self._constructors(system),
            )


class _ImportJobError(Exception, _ImportJobResult):

    def __init__(self, module_name, error_msg=None, traceback=None, missing_reqs=None):
        Exception.__init__(self, error_msg)
        _ImportJobResult.__init__(self, module_name, error_msg, traceback, missing_reqs)


class _IncompleteError(_ImportJobError):

    def make_result(self, recorder, module, key_to_req, system):
        system_reqs = self._used_system_reqs(key_to_req, system)
        import_reqs = self._imports_to_requirements(recorder.missing_imports | recorder.used_imports)
        return IncompleteImportResult(
            missing_reqs=self._missing_reqs,
            all_reqs=system_reqs | import_reqs,
            error=self._error_msg,
            traceback=self._traceback,
            )


class _FailedError(_ImportJobError):

    def make_result(self, recorder, module, key_to_req, system):
        return FailedImportResult(
            used_reqs=self._used_requirements(recorder, key_to_req, system),
            error=self._error_msg,
            traceback=self._traceback,
            )


class ImportJob(SystemJob):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg, rc_resource_creg, system_config_piece):
        return cls(
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            req_to_resources=cls.req_to_resources_from_pieces(
                rc_requirement_creg, rc_resource_creg, piece.req_to_resource),
            system_config_piece=system_config_piece,
            )

    def __init__(self, python_module_src, idx, req_to_resources, system_config_piece=None):
        super().__init__(python_module_src, system_config_piece, req_to_resources)
        self._idx = idx

    def __repr__(self):
        return f"<ImportJob {self._src.name}/{self._idx}>"

    @cached_property
    def piece(self):
        return htypes.import_job.job(
            python_module=self._src.piece,
            idx=self._idx,
            req_to_resource=self._req_to_resource_pieces,
            )

    def run(self):
        resources = [*enum_builtin_resources(self._src.name), *flatten(self._req_to_resources.values())]
        recorder_piece, module_piece = self._src.recorded_python_module(tag='import')
        system_resources = [*resources, *self._job_resources(module_piece)]
        system = None
        key_to_req = {}
        recorder = None
        module = None
        try:
            system = self.convert_errors(self._prepare_system, system_resources)
            key_to_req = self._make_key_to_req_map(system['cfg_item_creg'])
            _ = system['ctr_collector']
            recorder = pyobj_creg.animate(recorder_piece)
            module = self.convert_errors(pyobj_creg.animate, module_piece)
        except _ImportJobError as x:
            result = x
        else:
            result = _Succeeded(self._src.name)
        return result.make_result(recorder, module, key_to_req, system)

    def _job_resources(self, module_piece):
        yield from super()._job_resources(module_piece)
        mark_module_item = htypes.ctr_collector.mark_module_cfg_item(
            module=mosaic.put(module_piece),
            name=self._src.name,
            )
        yield ConfigItemResource(
            service_name='ctr_collector',
            template_ref=mosaic.put(mark_module_item),
            )

    def incomplete_error(self, error_msg, traceback=None, missing_reqs=None):
        raise _IncompleteError(self._src.name, error_msg, traceback[:-1] if traceback else None, missing_reqs)

    def failed_error(self, error_msg, traceback):
        raise _FailedError(self._src.name, error_msg, traceback)
