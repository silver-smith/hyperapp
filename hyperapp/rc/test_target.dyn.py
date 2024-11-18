from collections import defaultdict

from .code.rc_target import Target
from .code.type_req import TypeReq
from .code.import_resource import ImportResource
from .code.test_job import TestJob


class TestJobTarget(Target):

    def __init__(self, python_module_src, types, import_tgt, function, req_to_target, test_tgt, config_tgt, fixtures_deps=None, idx=1):
        self._src = python_module_src
        self._types = types
        self._import_tgt = import_tgt
        self._function = function
        self._req_to_target = req_to_target or {}
        self._test_tgt = test_tgt
        self._config_tgt = config_tgt
        self._tested_imports = set()  # import targets being tested.
        self._fixtures_deps = fixtures_deps or set()  # import targets with fixtures.
        self._tested_deps = set()  # targets required by tested code targets.
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
        result.update_targets(self, target_set)

    @property
    def src(self):
        return self._src

    @property
    def test_tgt(self):
        return self._test_tgt

    def add_fixtures_import(self, target):
        self._fixtures_deps.add(target)

    def add_tested_import(self, target):
        self._tested_imports.add(target)
        if target.completed:
            self._tested_deps |= target.deps

    def set_alias_completed(self):
        self._test_tgt.set_completed()

    @property
    def req_set(self):
        return set(self._req_to_target)

    def create_next_target(self, req_to_target):
        # Do not lose requirements from previous iterations.
        full_req_to_target = {
            **self._req_to_target,
            **req_to_target,
            }
        target = TestJobTarget(
            python_module_src=self._src,
            types=self._types,
            import_tgt=self._import_tgt,
            function=self._function,
            req_to_target=full_req_to_target,
            test_tgt=self._test_tgt,
            config_tgt=self._config_tgt,
            fixtures_deps=self._fixtures_deps,
            idx=self._idx + 1,
            )
        self._test_tgt.set_test_target(target)
        return target


class TestTarget(Target):

    def __init__(self, target_set, python_module_src, function):
        self._target_set = target_set
        self._src = python_module_src
        self._function = function
        self._test_target = None
        self._completed = False

    @property
    def name(self):
        return f'test/{self._src.name}/{self._function.name}'

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {self._test_target}

    def set_completed(self):
        self._completed = True

    def set_test_target(self, test_target):
        self._test_target = test_target
