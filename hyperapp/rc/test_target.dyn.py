from collections import defaultdict

from .code.rc_target import Target
from .code.type_req import TypeReq
from .code.import_resource import ImportResource
from .code.test_job import TestJob


class TestJobTarget(Target):

    def __init__(self, types, config_tgt, import_tgt, test_target, src, function, req_to_target,
                 tested_imports, fixtures_deps, tested_deps, idx=1):
        self._types = types
        self._config_tgt = config_tgt
        self._import_tgt = import_tgt
        self._test_target = test_target
        self._src = src
        self._function = function
        self._req_to_target = req_to_target
        self._tested_imports = tested_imports  # import targets being tested.
        self._fixtures_deps = fixtures_deps  # import targets with fixtures.
        self._tested_deps = tested_deps  # targets required by tested code targets.
        self._idx = idx
        self._completed = False
        self._ready = False

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
        # Note: Copy is at TestTarget.update_status method.
        for target in self._tested_imports:
            if target.completed:
                self._tested_deps |= target.deps
        self._ready = all(target.completed for target in self.deps)

    def make_job(self):
        return TestJob(self._src, self._idx, self._req_to_resources, self._function.name)

    @property
    def _req_to_resources(self):
        result = defaultdict(set)
        for src in self._types.as_list:
            req = TypeReq.from_type_src(src)
            result[req] = {ImportResource.from_type_src(src)}
        for req, target in self._req_to_target.items():
            result[req] |= set(req.make_resource_list(target))
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

    def __init__(self, cache, target_set, types, config_tgt, import_tgt, python_module_src, function, req_to_target):
        self._cache = cache
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
        # Note: Copy is at TestJobTarget.update_status method.
        for target in self._tested_imports:
            if target.completed:
                self._tested_deps |= target.deps

    @property
    def req_set(self):
        return set(self._req_to_target)

    def set_completed(self):
        self._completed = True
        self._current_job_target.set_completed()

    def set_test_target(self, test_target):
        self._test_target = test_target

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
        target = TestJobTarget(
            types=self._types,
            config_tgt=self._config_tgt,
            import_tgt=self._import_tgt,
            test_target=self,
            src=self._src,
            function=self._function,
            req_to_target=self._req_to_target,
            tested_imports=self._tested_imports,
            fixtures_deps=self._fixtures_deps,
            tested_deps=self._tested_deps,
            )
        self._current_job_target = target
        self._target_set.add(target)

    def _create_cache_target(self, entry):
        assert 0

    def add_fixtures_import(self, target):
        assert not self._current_job_target
        self._fixtures_deps.add(target)

    def add_tested_import(self, target):
        assert not self._current_job_target
        self._tested_imports.add(target)
        if target.completed:
            self._tested_deps |= target.deps

    def create_next_job_target(self, req_to_target):
        job_target = self._current_job_target
        assert isinstance(job_target, TestJobTarget)
        # Do not lose requirements from previous iterations.
        full_req_to_target = {
            **self._req_to_target,
            **req_to_target,
            }
        target = TestJobTarget(
            types=self._types,
            config_tgt=self._config_tgt,
            import_tgt=self._import_tgt,
            test_target=self,
            src=self._src,
            function=self._function,
            req_to_target=full_req_to_target,
            tested_imports=self._tested_imports,
            fixtures_deps=self._fixtures_deps,
            tested_deps=self._tested_deps,
            idx=job_target._idx + 1,
            )
        self._target_set.add(target)
        self._current_job_target = target
        return target
