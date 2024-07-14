from hyperapp.common.util import flatten
from hyperapp.resource.resource_module import AUTO_GEN_LINE

from .code.rc_constants import JobStatus
from .code.builtin_resources import enum_builtin_resources
from .code.import_resource import ImportResource
from .code.import_job import ImportJob
from .code.test_target import TestTargetAlias, TestTarget
from .code.python_module_resource_target import CompiledPythonModuleResourceTarget, ManualPythonModuleResourceTarget
from .code.custom_resource_registry import create_custom_resource_registry


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

    def __init__(self, python_module_src, type_src_list, custom_resource_registry):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._custom_resource_registry = custom_resource_registry
        self._completed = False
        self._deps = set()
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
        return self._deps

    def update_status(self):
        pass

    def set_completed(self, req_to_target):
        self._deps = {*req_to_target.values()}
        for req, target in req_to_target.items():
            resource = req.make_resource(target)
            if resource is None:
                continue  # TODO: Remove when all make_resource methods are implemented.
            self._resources.append(resource)
        self._completed = True

    def create_resource_target(self, all_imports_known_tgt):
        return CompiledPythonModuleResourceTarget(self._python_module_src, self._custom_resource_registry, all_imports_known_tgt, self)

    def recorded_python_module(self):
        type_resources = [
            ImportResource.from_type_src(src)
            for src in self._type_src_list
            ]
        all_resources = [*enum_builtin_resources(), *type_resources, *self._resources]
        import_list = flatten(d.import_records for d in all_resources)
        recorder_piece, module_piece = self._python_module_src.recorded_python_module(import_list)
        return (self._python_module_src.name, recorder_piece, module_piece)


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
        resources = [
            ImportResource.from_type_src(src)
            for src in self._type_src_list
            ]
        return ImportJob(self._python_module_src, self._idx, resources)

    def handle_job_result(self, target_set, result):
        self._completed = True
        result.update_targets(self, target_set)

    def set_alias_completed(self, req_to_target):
        self._alias.set_completed(req_to_target)

    def create_next_target(self, req_to_target):
        return ImportTarget(self._python_module_src, self._type_src_list, self._alias, self._idx + 1, req_to_target)

    def get_resource_target(self, target_factory):
        return target_factory.python_module_resource_by_src(self._python_module_src)

    def create_test_target(self, function, req_to_target):
        alias = TestTargetAlias(self._python_module_src, function)
        target = TestTarget(self._python_module_src, self._type_src_list, function, req_to_target, alias)
        return (alias, target)


def create_import_targets(root_dir, target_set, python_module_src_list, type_src_list):
    custom_resource_registry = create_custom_resource_registry(root_dir)
    all_imports_known_tgt = AllImportsKnownTarget()
    for src in python_module_src_list:
        if root_dir.joinpath(src.resource_path).read_text().startswith(AUTO_GEN_LINE):
            alias_tgt = ImportTargetAlias(src, type_src_list, custom_resource_registry)
            import_tgt = ImportTarget(src, type_src_list, alias_tgt)
            all_imports_known_tgt.add_import_target(import_tgt)
            target_set.add(import_tgt)
            target_set.add(alias_tgt)
        else:
            resource_tgt = ManualPythonModuleResourceTarget(src, custom_resource_registry)
            target_set.add(resource_tgt)
    target_set.add(all_imports_known_tgt)
