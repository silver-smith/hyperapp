from .code.rc_target import Target
from .code.import_resource import ImportResource
from .code.test_job import TestJob


def req_key(req_item):
    req = req_item[0]
    return (req.__class__.__name__, *req.__dict__.values())


class TestTargetAlias(Target):

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

    def set_completed(self, req_to_target):
        self._completed = True

    def set_test_target(self, test_target):
        self._test_target = test_target
        self._target_set.update_deps_for(self)


class TestTarget(Target):

    def __init__(self, python_module_src, types, import_tgt, function, req_to_target, alias, config_tgt, fixtures_deps=None, idx=1):
        self._src = python_module_src
        self._types = types
        self._import_tgt = import_tgt
        self._function = function
        self._req_to_target = req_to_target or {}
        self._alias = alias
        self._config_tgt = config_tgt
        self._tested_imports = set()  # import targets being tested.
        self._fixtures_deps = fixtures_deps or set()  # import alias targets with fixtures.
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
        resources = list(self._enum_resources())
        return TestJob(self._src, self._idx, resources, self._function.name)

    def _enum_resources(self):
        for src in self._types.as_list:
            yield ImportResource.from_type_src(src)
        for req, target in sorted(self._req_to_target.items(), key=req_key):
            yield from req.make_resource_list(target)
        yield from self._config_tgt.enum_ready_resources()
        yield from self._import_tgt.test_resources

    def handle_job_result(self, target_set, result):
        self._completed = True
        result.update_targets(self, target_set)

    @property
    def alias(self):
        return self._alias

    def add_fixtures_import(self, target):
        self._fixtures_deps.add(target)

    def add_tested_import(self, target):
        self._tested_imports.add(target)
        if target.completed:
            self._tested_deps |= target.deps

    def set_alias_completed(self, req_to_target):
        self._alias.set_completed(req_to_target)

    @property
    def req_set(self):
        return set(self._req_to_target)

    def create_next_target(self, req_to_target):
        # Do not lose requirements from previous iterations.
        full_req_to_target = {
            **self._req_to_target,
            **req_to_target,
            }
        target = TestTarget(
            python_module_src=self._src,
            types=self._types,
            import_tgt=self._import_tgt,
            function=self._function,
            req_to_target=full_req_to_target,
            alias=self._alias,
            config_tgt=self._config_tgt,
            fixtures_deps=self._fixtures_deps,
            idx=self._idx + 1,
            )
        self._alias.set_test_target(target)
        return target
