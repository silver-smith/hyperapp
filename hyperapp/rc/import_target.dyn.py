from functools import cached_property

from hyperapp.common.util import flatten

from .code.rc_target import Target
from .code.rc_constants import JobStatus
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


class ImportTargetAlias(Target):

    @staticmethod
    def name_for_src(python_module_src):
        return f'import/{python_module_src.name}'

    def __init__(self, python_module_src, custom_resource_registry, types):
        self._src = python_module_src
        self._types = types
        self._custom_resource_registry = custom_resource_registry
        self._import_target = None
        self._completed = False
        self._got_requirements = False
        self._req_to_target = {}
        self._test_constructors = set()

    def __repr__(self):
        return f"<ImportAliasTarget {self.name}>"

    @property
    def name(self):
        return self.name_for_src(self._src)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {self._import_target, *self._req_to_target.values()}

    def update_status(self):
        if self._got_requirements:
            self._completed = all(target.completed for target in self.deps)

    @property
    def module_name(self):
        return self._src.name

    def set_import_target(self, import_target):
        self._import_target = import_target

    def add_test_ctr(self, ctr):
        self._test_constructors.add(ctr)

    def set_requirements(self, req_to_target):
        self._req_to_target = req_to_target
        self._got_requirements = True
        self.update_status()

    def create_resource_target(self, resource_dir, all_imports_known_tgt):
        return CompiledPythonModuleResourceTarget(
            self._src, self._custom_resource_registry, resource_dir, self._types, all_imports_known_tgt, self)

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


class ImportTarget(Target):

    def __init__(self, target_set, python_module_src, types, alias, config_tgt, idx=1, req_to_target=None):
        self._target_set = target_set
        self._src = python_module_src
        self._types = types
        self._alias = alias
        self._config_tgt = config_tgt
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
        result.update_targets(self, target_set)

    @property
    def alias(self):
        return self._alias

    def set_alias_requirements(self, req_to_target):
        self._alias.set_requirements(req_to_target)

    def create_next_target(self, req_to_target):
        target = ImportTarget(self._target_set, self._src, self._types, self._alias, self._config_tgt, self._idx + 1, req_to_target)
        self._alias.set_import_target(target)
        return target

    def get_resource_target(self, target_factory):
        return target_factory.python_module_resource_by_src(self._src)

    def create_test_target(self, function, req_to_target):
        alias = TestTargetAlias(self._src, function)
        target = TestTarget(self._src, self._types, self._alias, function, req_to_target, alias, self._config_tgt)
        alias.set_test_target(target)
        return (alias, target)
