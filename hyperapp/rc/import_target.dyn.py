from hyperapp.common.util import flatten

from .code.rc_constants import JobStatus
from .code.builtin_resources import enum_builtin_resources
from .code.import_resource import ImportResource
from .code.import_job import ImportJob
from .code.test_target import TestTargetAlias, TestTarget
from .code.python_module_resource_target import CompiledPythonModuleResourceTarget


class AllImportsKnownTarget:

    name = 'all-imports-known'

    def __init__(self):
        self._import_targets = set()  # first import targets, not aliases.
        self._completed = False

    def __repr__(self):
        return f"<AllImportsKnownTarget>"

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return self._import_targets

    def update_status(self):
        self._completed = all(target.completed for target in self._import_targets)

    def add_import_target(self, target):
        self._import_targets.add(target)


class ImportTargetAlias:

    @staticmethod
    def name_for_src(python_module_src):
        return f'import/{python_module_src.name}'

    def __init__(self, python_module_src, custom_resource_registry, type_src_list):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._custom_resource_registry = custom_resource_registry
        self._completed = False
        self._got_requirements = False
        self._req_to_target = {}
        self._resources = []

    def __repr__(self):
        return f"<ImportAliasTarget {self.name}>"

    @property
    def name(self):
        return self.name_for_src(self._python_module_src)

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return set(self._req_to_target.values())

    def update_status(self):
        if self._got_requirements:
            self._completed = all(target.completed for target in self.deps)

    def set_requirements(self, req_to_target):
        self._req_to_target = req_to_target
        self._got_requirements = True
        self.update_status()

    def create_resource_target(self, resource_dir, all_imports_known_tgt):
        return CompiledPythonModuleResourceTarget(
            self._python_module_src, self._custom_resource_registry, resource_dir, self._type_src_list, all_imports_known_tgt, self)

    def recorded_python_module(self):
        assert self._completed
        type_resources = [
            ImportResource.from_type_src(src)
            for src in self._type_src_list
            ]
        all_resources = [*enum_builtin_resources(), *type_resources, *self._enum_resources()]
        import_list = flatten(d.import_records for d in all_resources)
        recorder_piece, module_piece = self._python_module_src.recorded_python_module(import_list)
        return (self._python_module_src.name, recorder_piece, module_piece)

    def _enum_resources(self):
        for req, target in self._req_to_target.items():
            resource = req.make_resource(target)
            if resource is None:
                continue  # TODO: Remove when all make_resource methods are implemented.
            yield resource


class ImportTarget:

    def __init__(self, python_module_src, type_src_list, alias, idx=1, req_to_target=None):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._alias = alias
        self._idx = idx
        self._req_to_target = req_to_target or {}
        self._completed = False
        self._ready = False

    def __repr__(self):
        return f"<ImportTarget {self.name}>"

    @property
    def name(self):
        return f'import/{self._python_module_src.name}/{self._idx}'

    @property
    def ready(self):
        return self._ready

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return self._req_to_target.values()

    def update_status(self):
        self._ready = all(target.completed for target in self._req_to_target.values())

    def make_job(self):
        resources = list(filter(None, self._enum_resources()))  # TODO: Remove filter when all make_resource methods are implemented.
        return ImportJob(self._python_module_src, self._idx, resources)

    def _enum_resources(self):
        for src in self._type_src_list:
            yield ImportResource.from_type_src(src)
        for req, target in self._req_to_target.items():
            yield req.make_resource(target)

    def handle_job_result(self, target_set, result):
        self._completed = True
        result.update_targets(self, target_set)

    def set_alias_requirements(self, req_to_target):
        self._alias.set_requirements(req_to_target)

    def create_next_target(self, req_to_target):
        return ImportTarget(self._python_module_src, self._type_src_list, self._alias, self._idx + 1, req_to_target)

    def get_resource_target(self, target_factory):
        return target_factory.python_module_resource_by_src(self._python_module_src)

    def create_test_target(self, function, req_to_target):
        alias = TestTargetAlias(self._python_module_src, function)
        target = TestTarget(self._python_module_src, self._type_src_list, function, req_to_target, alias)
        return (alias, target)
