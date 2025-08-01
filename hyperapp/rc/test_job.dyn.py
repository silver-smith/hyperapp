import inspect
import logging
from collections import defaultdict
from functools import cached_property

from hyperapp.boot.htypes import Type
from hyperapp.boot.config_key_error import ConfigKeyError
from hyperapp.boot.util import flatten, merge_dicts

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .code.system_fn import ContextFn
from .code.config_ctl import (
    DictConfigCtl,
    item_pieces_to_data,
    service_pieces_to_config,
    )
from .code.rc_constants import JobStatus
from .code.python_src import PythonModuleSrc
from .code.builtin_resources import enum_builtin_resources
from .code.import_recorder import IncompleteImportedObjectError, ImportRecorder
from .code.config_layer import MemoryConfigLayer, StaticConfigLayer
from .code.system import UnknownServiceError
from .code.system_probe import SystemProbe
from .code.system_job import Result, SystemJob, SystemJobResult

log  = logging.getLogger(__name__)
rc_log = logging.getLogger('rc')


class _SucceededTestResultBase(SystemJobResult):

    @staticmethod
    def _used_imports_to_dict(used_imports_list):
        result = {}
        for rec in used_imports_list:
            result[rec.module_name] = rec.imports
        return result

    def __init__(self, status, used_reqs, used_imports, error=None, traceback=None):
        super().__init__(status, used_reqs, error, traceback)
        self._used_imports = used_imports

    @property
    def _used_imports_pieces(self):
        return tuple(
            htypes.test_job.used_imports(
                module_name=module_name,
                imports=tuple(imports),
                )
            for module_name, imports in self._used_imports.items()
            )

    def _update_tested_imports(self, target_factory):
        for module_name, import_list in self._used_imports.items():
            resource_tgt = target_factory.python_module_resource_by_module_name(module_name)
            resource_tgt.add_used_imports(import_list)


class SucceededTestResult(_SucceededTestResultBase):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg, rc_constructor_creg):
        used_imports = cls._used_imports_to_dict(piece.used_imports)
        used_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.used_requirements)
        constructors = [
            rc_constructor_creg.invite(ref)
            for ref in piece.constructors
            ]
        return cls(used_reqs, used_imports, constructors)

    def __init__(self, used_reqs, used_imports, constructors):
        super().__init__(JobStatus.ok, used_reqs, used_imports)
        self._constructors = constructors

    @property
    def piece(self):
        return htypes.test_job.succeeded_result(
            used_requirements=tuple(mosaic.put(req.piece) for req in self._used_reqs),
            used_imports=self._used_imports_pieces,
            constructors=tuple(mosaic.put(ctr.piece) for ctr in self._constructors),
            )

    def cache_target_name(self, my_target):
        return my_target.test_target.name

    @property
    def used_reqs(self):
        return self._used_reqs

    def update_targets(self, test_target, target_set):
        self._update_tested_imports(target_set.factory)
        self._update_ctr_targets(target_set)
        test_target.set_completed()

    def _update_ctr_targets(self, target_set):
        for ctr in self._constructors:
            ctr.update_targets(target_set)


class IncompleteTestResult(_SucceededTestResultBase):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg):
        missing_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.missing_requirements)
        used_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.used_requirements)
        used_imports = cls._used_imports_to_dict(piece.used_imports)
        return cls(missing_reqs, used_reqs, used_imports, piece.error, piece.traceback)

    def __init__(self, missing_reqs, used_reqs, used_imports, error, traceback):
        super().__init__(JobStatus.incomplete, used_reqs, used_imports, error, traceback)
        self._missing_reqs = missing_reqs

    @property
    def piece(self):
        return htypes.test_job.incomplete_result(
            missing_requirements=tuple(mosaic.put(req.piece) for req in self._missing_reqs),
            used_requirements=tuple(mosaic.put(req.piece) for req in self._used_reqs),
            used_imports=self._used_imports_pieces,
            error=self.error,
            traceback=tuple(self.traceback),
            )

    @property
    def _reqs_desc(self):
        return ", ".join(r.desc for r in self._missing_reqs if r.desc)

    @property
    def desc(self):
        return super().desc + f", needs {self._reqs_desc}"

    def update_targets(self, test_target, target_set):
        self._update_tested_imports(target_set.factory)
        req_to_target = self._resolve_requirements(target_set.factory, self._missing_reqs | self._used_reqs)
        if set(req_to_target) <= test_target.req_set:
            # No new requirements are discovered.
            raise RuntimeError(f"{test_target.name}: Infinite loop detected with: {self._reqs_desc}")
        else:
            test_target.create_next_job_target(req_to_target)


class FailedTestResult(SystemJobResult):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg):
        used_reqs = cls._resolve_reqirement_refs(rc_requirement_creg, piece.used_requirements)
        return cls(used_reqs, piece.error, piece.traceback)

    def __init__(self, used_reqs, error, traceback):
        super().__init__(JobStatus.failed, used_reqs, error, traceback)

    @property
    def piece(self):
        return htypes.test_job.failed_result(
            used_requirements=tuple(mosaic.put(req.piece) for req in self._used_reqs),
            error=self.error,
            traceback=tuple(self.traceback),
            )

    def update_targets(self, test_target, target_set):
        pass


def _catch_errors(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except UnknownServiceError as x:
        raise htypes.rc_job.unknown_service_error(x.service_name) from x
    except ConfigKeyError as x:
        if isinstance(x.key, Type):
            key_ref = pyobj_creg.actor_to_ref(x.key)
        else:
            raise  # Do not treat data registry miss as incomplete jobs.
            # key_ref = mosaic.put(x.key)
        raise htypes.rc_job.config_key_error(x.service_name, key_ref) from x
    except Exception as x:
        raise RuntimeError(f"In test servant {fn}: {x}") from x


def rpc_servant_wrapper(_real_servant_ref, **kw):
    servant = pyobj_creg.invite(_real_servant_ref)
    return _catch_errors(servant, **kw)


def rpc_system_servant_wrapper(_real_fn_piece, system_fn_creg, **kw):
    real_fn = system_fn_creg.animate(_real_fn_piece)
    ctx = Context(**kw)
    return _catch_errors(real_fn.call, ctx)


def rpc_service_wrapper(system, _real_service_name, **kw):
    def run():
        service = system.resolve_service(_real_service_name)
        return service(**kw)
    return _catch_errors(run)


def test_subprocess_rpc_main(connection, received_refs, system_config_piece, root_name, **kw):
    system = SystemProbe()
    system.load_static_config(system_config_piece)
    system.load_config_layer('memory', MemoryConfigLayer(system))
    system.set_default_layer('memory')
    ImportRecorder.configure_pyobj_creg(system)
    _ = system.resolve_service('marker_registry')  # Init markers.
    system['init_hook'].run_hooks()
    system.run(root_name, connection, received_refs, **kw)


class _TestJobResult(Result):

    @staticmethod
    def _used_imports(resources, system):
        if not system:
            # Without system recorders will be created without resources and cached by pyobj_creg.
            return {}
        recorder_dict = merge_dicts(d.recorders for d in resources)
        return {
            module_name: recorder.used_imports
            for module_name, recorder in recorder_dict.items()
            }


class _Succeeded(_TestJobResult):

    def __init__(self, module_name, import_reqs):
        super().__init__(module_name)
        self._import_reqs = import_reqs

    def make_result(self, resources, recorder, key_to_req, system):
        return SucceededTestResult(
            used_reqs=self._used_requirements(recorder, key_to_req, system) | self._import_reqs,
            used_imports=self._used_imports(resources, system),
            constructors=self._constructors(system),
            )


class _TestJobError(Exception, _TestJobResult):

    def __init__(self, module_name, error_msg=None, traceback=None, missing_reqs=None):
        Exception.__init__(self, error_msg)
        _TestJobResult.__init__(self, module_name, error_msg, traceback, missing_reqs)


class _IncompleteError(_TestJobError):

    def make_result(self, resources, recorder, key_to_req, system):
        return IncompleteTestResult(
            missing_reqs=self._missing_requirements(recorder),
            used_reqs=self._used_requirements(recorder, key_to_req, system),
            used_imports=self._used_imports(resources, system),
            error=self._error_msg,
            traceback=self._traceback,
            )


class _FailedError(_TestJobError):

    def make_result(self, resources, recorder, key_to_req, system):
        return FailedTestResult(
            used_reqs=self._used_requirements(recorder, key_to_req, system),
            error=self._error_msg,
            traceback=self._traceback,
            )


class TestJob(SystemJob):

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg, rc_resource_creg):
        return cls(
            rc_config=piece.rc_config,
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            req_to_resources=cls.req_to_resources_from_pieces(
                rc_requirement_creg, rc_resource_creg, piece.req_to_resource),
            import_reqs={rc_requirement_creg.invite(ref) for ref in piece.import_reqs},
            test_fn_name=piece.test_fn_name,
            )

    def __init__(self, rc_config, python_module_src, idx, req_to_resources, import_reqs, test_fn_name):
        super().__init__(rc_config, python_module_src, req_to_resources)
        self._idx = idx
        # Requirement set. Requirements collected by import job.
        # Second import recorder usage in the same process does not yield requirements yielded during import.
        # So, preserve them - they are actually used.
        self._import_reqs = import_reqs
        self._test_fn_name = test_fn_name

    def __repr__(self):
        return f"<TestJob {self._src.name}/{self._test_fn_name}/{self._idx}>"

    @cached_property
    def piece(self):
        return htypes.test_job.job(
            rc_config=self._rc_config,
            python_module=self._src.piece,
            idx=self._idx,
            req_to_resource=self._req_to_resource_pieces,
            import_reqs=tuple(mosaic.put(req.piece) for req in self._import_reqs),
            test_fn_name=self._test_fn_name,
            )

    def run(self):
        resources = [*enum_builtin_resources(self._src.name), *flatten(self._req_to_resources.values())]
        recorder_piece, module_piece = self._src.recorded_python_module(tag='test')
        system = None
        key_to_req = {}
        recorder = None
        try:
            system = self.convert_errors(self._prepare_system, resources)
            cfg_item_creg = system['cfg_item_creg']
            key_to_req = self._make_key_to_req_map(cfg_item_creg)
            ctr_collector = system['ctr_collector']
            recorder = pyobj_creg.animate(recorder_piece)
            ctr_collector.ignore_module(module_piece)
            module = self.convert_errors(pyobj_creg.animate, module_piece)
            root_fixture_config = self._root_fixture_config_layer(system, cfg_item_creg, module_piece, module)
            system.load_config_layer('rc-test-root', root_fixture_config)
            self.convert_errors(self._run_system, system)
        except _TestJobError as x:
            result = x
        else:
            result = _Succeeded(self._src.name, self._import_reqs)
        return result.make_result(resources, recorder, key_to_req, system)

    def _run_system(self, system):
        rpc_servant_wrapper = system['rpc_servant_wrapper']
        rpc_system_servant_wrapper = system['rpc_system_servant_wrapper']
        rpc_service_wrapper = system['rpc_service_wrapper']
        subprocess_rpc_main = system['subprocess_rpc_main']
        rpc_system_call_factory = system['rpc_system_call_factory']
        rpc_servant_wrapper.set(self._wrap_rpc_servant)
        rpc_system_servant_wrapper.set(self._wrap_rpc_system_servant, rpc_system_call_factory)
        rpc_service_wrapper.set(self._wrap_rpc_service)
        subprocess_rpc_main.set(test_subprocess_rpc_main)
        try:
            return system.run(self._root_name)
        finally:
            subprocess_rpc_main.reset()
            rpc_service_wrapper.reset()
            rpc_servant_wrapper.reset()

    @property
    def _root_name(self):
        return self._test_fn_name

    def _root_fixture_config_layer(self, system, cfg_item_creg, module_piece, module):
        ctl = DictConfigCtl(cfg_item_creg=cfg_item_creg)
        test_fn = getattr(module, self._test_fn_name)
        fn_piece = htypes.builtin.attribute(
            object=mosaic.put(module_piece),
            attr_name=self._test_fn_name,
            )
        template = htypes.fixture_resource.fixture_probe_template(
            service_name=self._test_fn_name,
            ctl=mosaic.put(ctl.piece),
            function=mosaic.put(fn_piece),
            params=tuple(inspect.signature(test_fn).parameters),
            )
        cfg_item = htypes.cfg_item.str_cfg_item(
            key=self._test_fn_name,
            value=mosaic.put(template),
            )
        service_to_config_piece = {
            'system': item_pieces_to_data([cfg_item])
            }
        config_piece = service_pieces_to_config(service_to_config_piece)
        return StaticConfigLayer(system, system['config_ctl'], config_piece)

    def incomplete_error(self, module_name, error_msg, traceback=None, missing_reqs=None):
        raise _IncompleteError(module_name, error_msg, traceback[:-1] if traceback else None, missing_reqs)

    def failed_error(self, module_name, error_msg, traceback):
        raise _FailedError(module_name, error_msg, traceback)

    def _wrap_rpc_servant(self, servant_ref, kw):
        wrapped_servant_ref = pyobj_creg.actor_to_ref(rpc_servant_wrapper)
        wrapped_kw = {'_real_servant_ref': servant_ref, **kw}
        return (wrapped_servant_ref, wrapped_kw)

    def _wrap_rpc_system_servant(self, rpc_system_call_factory, fn, kw):
        wrapped_fn = ContextFn(
            rpc_system_call_factory=rpc_system_call_factory,
            ctx_params=('_real_fn_piece', *fn.ctx_params),
            service_params=('system_fn_creg',),
            raw_fn=rpc_system_servant_wrapper,
            )
        wrapped_kw = {'_real_fn_piece': fn.piece, **kw}
        return (wrapped_fn, wrapped_kw)

    def _wrap_rpc_service(self, service_name, kw):
        wrapped_kw = {'_real_service_name': service_name, **kw}
        return ('test_job_rpc_service_wrapper', wrapped_kw)
