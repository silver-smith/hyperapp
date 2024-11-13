from functools import cached_property

from hyperapp.common.util import flatten

from .code.rc_target import Target
from .code.builtin_resources import enum_builtin_resources
from .code.import_resource import ImportResource
from .code.import_job import ImportJob
from .code.test_target import TestTargetAlias, TestTarget
from .code.python_module_resource_target import CompiledPythonModuleResourceTarget


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
        self._import_targets.add(target)

    def init_completed(self):
        self._init_completed = True
        self.update_status()


class ImportCachedTarget(Target):

    def __init__(self, target_set, types, config_tgt, all_imports_known_tgt, import_tgt, src, deps, req_to_target, job_result):
        self._target_set = target_set
        self._types = types
        self._config_tgt = config_tgt
        self._import_tgt = import_tgt
        self._all_imports_known_tgt = all_imports_known_tgt
        self._src = src
        self._deps = deps  # requirement -> resource set
        self._req_to_target = req_to_target
        self._job_result = job_result
        self._completed = False
        self._ready = False

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
        target = ImportJobTarget(self._target_set, self._types, self._config_tgt, self._import_tgt, self._src, req_to_target=self._req_to_target)
        self._target_set.add(target)
        self._import_tgt.set_current_job_target(target)
        self._all_imports_known_tgt.add_import_target(target)
        self._target_set.update_deps_for(self._all_imports_known_tgt)
        return target

    def _use_job_result(self):
        self._job_result.update_targets(self._import_tgt, self._target_set)


class ImportJobTarget(Target):

    def __init__(self, target_set, types, config_tgt, import_tgt, src, idx=1, req_to_target=None):
        self._target_set = target_set
        self._types = types
        self._config_tgt = config_tgt
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
        resources = list(self._enum_resources())
        return ImportJob(self._src, self._idx, resources)

    def _enum_resources(self):
        for src in self._types.as_list:
            yield ImportResource.from_type_src(src)
        for req, target in self._req_to_target.items():
            yield from req.make_resource_list(target)
        # Some modules, like common.mark, are used before all imports are stated.
        for target in self._target_set.completed_python_module_resources:
            yield ImportResource(['code', target.code_name], target.python_module_piece)

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
    def name_for_src(python_module_src):
        return f'import/{python_module_src.name}'

    def __init__(self, cache, target_set, custom_resource_registry, types, config_tgt, all_imports_known_tgt, python_module_src):
        self._cache = cache
        self._target_set = target_set
        self._custom_resource_registry = custom_resource_registry
        self._types = types
        self._config_tgt = config_tgt
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

    def check_cache(self):
        try:
            entry = self._cache[self.name]
        except KeyError:
            pass
        else:
            if entry.src == self._src:
                self._create_cache_target(entry)
                return
        self._create_job_target()

    def _create_job_target(self):
        target = ImportJobTarget(self._target_set, self._types, self._config_tgt, self, self._src, idx=1)
        self._init_current_job_target(target)
        self._all_imports_known_tgt.add_import_target(target)
        self._target_set.update_deps_for(self._all_imports_known_tgt)

    def _create_cache_target(self, entry):
        entry.result.non_ready_update_targets(self, self._target_set)
        req_to_target = self._resolve_requirements(entry.deps.keys())
        target = ImportCachedTarget(
            self._target_set, self._types, self._config_tgt, self._all_imports_known_tgt,
            self, self._src, entry.deps, req_to_target, entry.result)
        self._init_current_job_target(target)

    def _resolve_requirements(self, requirements):
        req_to_target = {}
        for req in requirements:
            target = req.get_target(self._target_set.factory)
            req_to_target[req] = target
        return req_to_target

    def _init_current_job_target(self, target):
        self._current_job_target = target
        self._target_set.add(target)
        target.update_status()
        self._target_set.update_deps_for(self)

    @property
    def module_name(self):
        return self._src.name

    def set_current_job_target(self, target):
        self._current_job_target = target
        self._target_set.update_deps_for(self)

    def add_test_ctr(self, ctr):
        self._test_constructors.add(ctr)

    def set_requirements(self, req_to_target):
        self._req_to_target = req_to_target
        self._got_requirements = True
        self.update_status()

    def create_resource_target(self, resource_dir):
        return CompiledPythonModuleResourceTarget(
            self._src, self._custom_resource_registry, resource_dir, self._types, self._all_imports_known_tgt, self)

    def get_resource_target(self, target_factory):
        return target_factory.python_module_resource_by_src(self._src)

    def create_next_job_target(self, req_to_target):
        job_tgt = self._current_job_target
        assert isinstance(job_tgt, ImportJobTarget)
        target = ImportJobTarget(self._target_set, self._types, self._config_tgt, self, self._src, job_tgt._idx + 1, req_to_target)
        self.set_current_job_target(target)
        return target

    def create_test_target(self, function, req_to_target):
        alias = TestTargetAlias(self._target_set, self._src, function)
        target = TestTarget(self._src, self._types, self, function, req_to_target, alias, self._config_tgt)
        alias.set_test_target(target)
        return (alias, target)

    @cached_property
    def recorded_python_module(self):
        assert self._completed
        import_list = flatten(d.import_records for d in self._enum_resources())
        recorder_piece, module_piece = self._src.recorded_python_module(import_list)
        return (self._src.name, recorder_piece, module_piece)

    @property
    def test_resources(self):
        module_name, recorder_piece, python_module = self.recorded_python_module
        return [
            ctr.make_resource(self._types, self._src.name, python_module)
            for ctr in self._test_constructors
            ]

    def _enum_resources(self):
        yield from enum_builtin_resources()
        for src in self._types.as_list:
            yield ImportResource.from_type_src(src)
        for req, target in self._req_to_target.items():
            yield from req.make_resource_list(target)
