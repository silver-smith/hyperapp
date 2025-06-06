import logging
from collections import defaultdict
from functools import cached_property

from hyperapp.boot.util import flatten

from .code.rc_target import Target
from .code.type_req import TypeReq
from .code.import_resource import ImportResource
from .code.import_job import ImportJob
from .code.test_target import TestTarget
from .code.python_module_resource_target import PythonModuleReq, CompiledPythonModuleResourceTarget
from .code.utils import iter_types

rc_log = logging.getLogger('rc')


def _resolve_requirements(target_factory, requirements):
    req_to_target = {}
    for req in requirements:
        target = req.get_target(target_factory)
        req_to_target[req] = target
    return req_to_target


class AllImportsKnownTarget(Target):

    name = 'all-imports-known'

    def __init__(self):
        self._import_targets = set()  # first import targets, not aliases.
        self._init_completed = False
        self._completed = False

    def __repr__(self):
        return f"<AllImportsKnownTarget>"

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return self._import_targets

    def update_status(self):
        if not self._init_completed:
            return
        self._completed = all(target.completed for target in self._import_targets)

    def add_import_target(self, target):
        assert not self._completed
        self._import_targets.add(target)

    def init_completed(self):
        self._init_completed = True


class ImportCachedTarget(Target):

    def __init__(self, rc_config, cached_count, target_set, types, import_tgt, src, deps, req_to_target, job_result):
        self._rc_config = rc_config
        self._cached_count = cached_count
        self._target_set = target_set
        self._types = types
        self._import_tgt = import_tgt
        self._src = src
        self._deps = deps  # requirement -> resource set
        self._req_to_target = req_to_target
        self._job_result = job_result
        self._completed = False

    @property
    def name(self):
        return f'import/{self._src.name}/cached'

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return set(self._req_to_target.values())

    def update_status(self):
        if self._completed:
            return
        if not all(target.completed for target in self._req_to_target.values()):
            return
        # Second resolve may shift from resolved to complete target.
        self._req_to_target = _resolve_requirements(self._target_set.factory, self._req_to_target)
        if all(target.completed for target in self._req_to_target.values()):
            self._completed = True  # Should be set before using job result for import target to become completed.
            self._check_deps()

    def _check_deps(self):
        for req, target in self._req_to_target.items():
            dep_resources = self._deps[req]
            actual_resources = set(req.make_resource_list(target))
            if actual_resources != dep_resources:
                self._create_job_target()
                return
        self._use_job_result()

    def _create_job_target(self):
        target = ImportJobTarget(self._rc_config, self._target_set, self._types, self._import_tgt, self._src, req_to_target=self._req_to_target)
        self._target_set.add(target)
        self._import_tgt.set_current_job_target(target)
        return target

    def _use_job_result(self):
        self._job_result.update_targets(self._import_tgt, self._target_set)
        self._cached_count.incr()
        rc_log.debug("%s: %s", self.name, self._job_result.desc)


class ImportJobTarget(Target):

    def __init__(self, rc_config, target_set, types, import_tgt, src, idx=1, req_to_target=None):
        self._rc_config = rc_config
        self._target_set = target_set
        self._types = types
        self._import_tgt = import_tgt
        self._src = src
        self._idx = idx
        self._req_to_target = req_to_target or {}
        self._completed = False
        self._ready = False

    @property
    def name(self):
        return f'import/{self._src.name}/{self._idx}'

    @property
    def ready(self):
        return self._ready

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return set(self._req_to_target.values())

    def update_status(self):
        self._ready = all(target.completed for target in self._req_to_target.values())

    def make_job(self):
        return ImportJob(self._rc_config, self._src, self._idx, self._req_to_resources)

    @property
    def _req_to_resources(self):
        result = defaultdict(set)
        for module_name, name, piece in iter_types(self._types):
            req = TypeReq(module_name, name)
            result[req] = {ImportResource.for_type(module_name, name, piece)}
        for req, target in self._req_to_target.items():
            result[req] |= set(req.make_resource_list(target))
        for req, resource_set in self._target_set.ready_req_to_resources.items():
            result[req] |= resource_set
        # Some modules, like base.mark, are used before all imports are stated.
        for target in self._target_set.completed_python_module_resources:
            req = PythonModuleReq(self._src.name, target.code_name)
            result[req] = {ImportResource(self._src.name, ['code', target.code_name], target.python_module_piece)}
        return dict(result)

    def handle_job_result(self, target_set, result):
        self._completed = True
        result.update_targets(self._import_tgt, target_set)

    @property
    def src(self):
        return self._src

    @property
    def import_tgt(self):
        return self._import_tgt


class ImportTarget(Target):

    @staticmethod
    def name_for_module_name(module_name):
        return f'import/{module_name}'

    @staticmethod
    def name_for_src(python_module_src):
        return f'import/{python_module_src.name}'

    def __init__(self, rc_config, cache, cached_count, target_set, custom_resource_registry, types, all_imports_known_tgt, python_module_src):
        self._rc_config = rc_config
        self._cache = cache
        self._cached_count = cached_count
        self._target_set = target_set
        self._custom_resource_registry = custom_resource_registry
        self._types = types
        self._all_imports_known_tgt = all_imports_known_tgt
        self._src = python_module_src
        self._current_job_target = None
        self._completed = False
        self._got_requirements = False
        self._req_to_target = {}
        self._test_constructors = set()

    @property
    def name(self):
        return self.name_for_src(self._src)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {self._current_job_target, *self._req_to_target.values()}

    def update_status(self):
        if self._got_requirements:
            self._completed = all(target.completed for target in self.deps)

    def create_job_target(self):
        try:
            entry = self._cache[self.name]
        except KeyError:
            pass
        else:
            if entry.src == self._src:
                self._create_cached_target(entry)
                return
        self._create_job_target()

    @property
    def types(self):
        return self._types

    def _create_job_target(self):
        target = ImportJobTarget(self._rc_config, self._target_set, self._types, self, self._src, idx=1)
        self._init_current_job_target(target)
        self._all_imports_known_tgt.add_import_target(target)

    def _create_cached_target(self, entry):
        entry.result.non_ready_update_targets(self, self._target_set)
        req_to_target = _resolve_requirements(self._target_set.factory, entry.deps.keys())
        target = ImportCachedTarget(
            self._rc_config, self._cached_count, self._target_set, self._types,
            self, self._src, entry.deps, req_to_target, entry.result)
        self._init_current_job_target(target)

    def _init_current_job_target(self, target):
        self._current_job_target = target
        self._target_set.add(target)

    @property
    def module_name(self):
        return self._src.name

    @property
    def import_requirements(self):
        return self._req_to_target.keys()

    def set_current_job_target(self, target):
        self._current_job_target = target

    def add_test_ctr(self, ctr):
        self._test_constructors.add(ctr)

    def set_requirements(self, req_to_target):
        for req in req_to_target:
            import_req = req.to_import_req()
            self._req_to_target[import_req] = import_req.get_target(self._target_set.factory)
        self._got_requirements = True

    def create_resource_target(self, resource_dir):
        return CompiledPythonModuleResourceTarget(
            self._target_set, self._src, self._custom_resource_registry, resource_dir, self._types, self._all_imports_known_tgt, self)

    def get_resource_target(self, target_factory):
        return target_factory.python_module_resource_by_module_name(self.module_name)

    def create_next_job_target(self, req_to_target):
        job_tgt = self._current_job_target
        assert isinstance(job_tgt, ImportJobTarget)
        target = ImportJobTarget(self._rc_config, self._target_set, self._types, self, self._src, job_tgt._idx + 1, req_to_target)
        self.set_current_job_target(target)
        return target

    def create_test_target(self, function, req_to_target):
        test_req_to_target = {}
        for req, target in req_to_target.items():
            import_req = req.to_test_req()
            test_req_to_target[import_req] = import_req.get_target(self._target_set.factory)
        test_target = TestTarget(
            self._rc_config, self._cache, self._cached_count, self._target_set, self._types,
            self, self._src, function, test_req_to_target)
        for req, target in req_to_target.items():
            req.apply_test_target(target, test_target, self._target_set)
        self._target_set.add(test_target)
        test_target.create_job_target()

    def recorded_python_module(self, tag):
        assert self._completed
        recorder_piece, module_piece = self._src.recorded_python_module(tag)
        return (self._src.name, recorder_piece, module_piece)

    @property
    def python_module_piece(self):
        recorder_piece, module_piece = self._src.recorded_python_module(tag='test')
        return module_piece

    @property
    def test_resources(self):
        return set(self._enum_test_resources())

    def _enum_test_resources(self):
        module_name, recorder_piece, python_module = self.recorded_python_module(tag='test')
        for ctr in self._test_constructors:
            yield ctr.make_resource(self._types, self._src.name, python_module)
