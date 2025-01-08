import logging
from collections import defaultdict

from .code.rc_target import TargetMissingError, Target
from .code.type_req import TypeReq
from .code.import_resource import ImportResource
from .code.python_module_resource_target import ImportPythonModuleReq, PythonModuleReq
from .code.test_job import TestJob

rc_log = logging.getLogger('rc')


def _resolve_requirements(target_factory, requirements):
    req_to_target = {}
    for req in requirements:
        target = req.get_target(target_factory)
        req_to_target[req] = target
    return req_to_target


class TestCachedTarget(Target):

    def __init__(self, cached_count, target_set, test_target, src, function, deps, req_to_target, job_result):
        self._cached_count = cached_count
        self._target_set = target_set
        self._test_target = test_target
        self._src = src
        self._function = function
        self._deps = deps
        self._req_to_target = req_to_target
        self._job_result = job_result
        self._completed = False

    @property
    def name(self):
        return f'test/{self._src.name}/{self._function.name}/cached'

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
        # If target is not one of our tested modules, second resolve shifts from resolved to complete target.
        self._req_to_target = _resolve_requirements(self._target_set.factory, self._req_to_target)
        if all(target.completed for target in self._req_to_target.values()):
            self._check_deps()
            self._completed = True

    def set_completed(self):
        pass  # Set in update_status.

    def _deps_match(self):
        for req, target in self._req_to_target.items():
            dep_resources = self._deps[req]
            actual_resources = set(req.make_resource_list(target))
            if actual_resources != dep_resources:
                return False
        return True

    # TODO: We may compare deps resources before all targets are completed. Thus, when they differ, job will be fired sooner.
    def _check_deps(self):
        try:
            if self._deps_match():
                self._use_job_result()
                return
        except TargetMissingError:
            pass
        self._create_job_target()

    def _create_job_target(self):
        self._test_target.create_first_job_target()

    def _use_job_result(self):
        self._job_result.update_targets(self._test_target, self._target_set)
        self._cached_count.incr()
        rc_log.debug("%s: %s", self.name, self._job_result.desc)


class TestJobTarget(Target):

    def __init__(self, target_set, types, config_tgt, import_tgt, test_target, src, function, req_to_target,
                 tested_imports, fixtures_deps, tested_deps, idx):
        self._target_set = target_set
        self._types = types
        self._config_tgt = config_tgt
        self._import_tgt = import_tgt
        self._test_target = test_target
        self._src = src
        self._function = function
        self._req_to_target = req_to_target
        self._tested_imports = tested_imports  # import targets being tested.
        self._picked_import_from_tested_import_tgt = set()
        self._fixtures_deps = fixtures_deps  # import targets with fixtures.
        self._tested_deps = tested_deps  # targets required by tested code targets.
        self._idx = idx
        self._completed = False
        self._ready = False
        self._tested_modules = set()  # Tested module full names
        for req in self._req_to_target:
            self._tested_modules |= req.tested_modules(self._target_set)

    @property
    def name(self):
        return f'test/{self._src.name}/{self._function.name}/{self._idx}'

    @property
    def ready(self):
        return self._ready

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {*self._tested_imports, *self._fixtures_deps, *self._tested_deps, *self._req_to_target.values()}

    def update_status(self):
        for tested_import_tgt in self._tested_imports:
            self._pick_import_from_tested_import_tgt(tested_import_tgt)
        if not all(target.completed for target in self.deps):
            return
        # if target is not one of our tested modules, second resolve shifts from resolved to complete target.
        self._req_to_target = _resolve_requirements(self._target_set.factory, self._req_to_target)
        self._ready = all(target.completed for target in self.deps)

    def _pick_import_from_tested_import_tgt(self, tested_import_tgt):
        if not tested_import_tgt.completed:
            return
        if tested_import_tgt in self._picked_import_from_tested_import_tgt:
            return
        self._tested_deps |= tested_import_tgt.deps
        for import_req in tested_import_tgt.import_requirements:
            if (isinstance(import_req, ImportPythonModuleReq)
                    and self._target_set.full_module_name(import_req.code_name) in self._tested_modules):
                # Tested module imported from another tested module.
                req = import_req
            else:
                req = import_req.to_test_req()
            self._req_to_target[req] = req.get_target(self._target_set.factory)
        self._picked_import_from_tested_import_tgt.add(tested_import_tgt)

    def make_job(self):
        return TestJob(self._src, self._idx, self._req_to_resources, self._function.name)

    @property
    def _req_to_resources(self):
        result = defaultdict(set)
        for src in self._types.as_list:
            req = TypeReq.from_type_src(src)
            result[req] = {ImportResource.from_type_src(src)}
        req_resources = set()
        tested_modules = set()
        for req, target in self._req_to_target.items():
            resources = set(req.make_resource_list(target))
            result[req] |= resources
            req_resources |= resources
            for res in resources:
                tested_modules |= set(res.tested_modules)
        for target in self._target_set.completed_python_module_resources:
            req = PythonModuleReq(self._src.name, target.code_name)
            result[req] = {ImportResource(self._src.name, ['code', target.code_name], target.python_module_piece)}
        for req, resource_set in self._config_tgt.ready_req_to_resources().items():
            result[req] |= resource_set
        return dict(result)

    def handle_job_result(self, target_set, result):
        self._completed = True
        result.update_targets(self._test_target, target_set)

    @property
    def src(self):
        return self._src

    @property
    def test_target(self):
        return self._test_target

    def set_completed(self):
        self._completed = True


class TestTarget(Target):

    def __init__(self, cache, cached_count, target_set, types, config_tgt, import_tgt, python_module_src, function, req_to_target):
        self._cache = cache
        self._cached_count = cached_count
        self._target_set = target_set
        self._types = types
        self._config_tgt = config_tgt
        self._import_tgt = import_tgt
        self._src = python_module_src
        self._function = function
        self._req_to_target = req_to_target
        self._current_job_target = None
        self._tested_imports = set()  # import targets being tested.
        self._fixtures_deps = set()  # import targets with fixtures.
        self._tested_deps = set()  # targets required by tested code targets.
        self._completed = False

    @property
    def name(self):
        return f'test/{self._src.name}/{self._function.name}'

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {*self._tested_imports, self._current_job_target}

    def update_status(self):
        # TODO: Check where to copy tested import picking from TestJobTarget.update_status method.
        for target in self._tested_imports:
            if target.completed:
                self._tested_deps |= target.deps
        if all(dep.completed for dep in self.deps):
            self._completed = True

    @property
    def req_set(self):
        return set(self._req_to_target)

    def set_completed(self):
        self._current_job_target.set_completed()

    def set_test_target(self, test_target):
        self._test_target = test_target

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

    def _create_job_target(self, req_to_target=None, idx=1):
        if req_to_target is None:
            req_to_target = self._req_to_target
        target = TestJobTarget(
            target_set=self._target_set,
            types=self._types,
            config_tgt=self._config_tgt,
            import_tgt=self._import_tgt,
            test_target=self,
            src=self._src,
            function=self._function,
            req_to_target=req_to_target,
            tested_imports=self._tested_imports,
            fixtures_deps=self._fixtures_deps,
            tested_deps=self._tested_deps,
            idx=idx,
            )
        self._current_job_target = target
        self._target_set.add(target)

    def _create_cached_target(self, entry):
        req_to_target = _resolve_requirements(self._target_set.factory, entry.deps.keys())
        target = TestCachedTarget(self._cached_count, self._target_set, self, self._src, self._function, entry.deps, req_to_target, entry.result)
        self._current_job_target = target
        self._target_set.add(target)

    def add_fixtures_import(self, target):
        assert not self._current_job_target
        self._fixtures_deps.add(target)

    def add_tested_import(self, target):
        assert not self._current_job_target
        self._tested_imports.add(target)
        if target.completed:
            self._tested_deps |= target.deps

    def create_first_job_target(self):
        self._create_job_target()

    def create_next_job_target(self, req_to_target):
        assert isinstance(self._current_job_target, TestJobTarget)
        current_idx = self._current_job_target._idx
        # Do not lose requirements from previous iterations.
        full_req_to_target = {
            **self._req_to_target,
            **req_to_target,
            }
        self._create_job_target(full_req_to_target, current_idx + 1)
