from .code.rc_constants import JobStatus
from .code.import_resource import ImportResource
from .code.import_job import ImportJob
from .code.test_target import TestTarget


class AllImportsKnownTarget:

    def __init__(self, import_targets):
        self._import_targets = import_targets
        self._completed = False

    @property
    def name(self):
        return 'all-imports-known'

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


class ImportTargetAlias:

    def __init__(self, python_module_src):
        self._python_module_src = python_module_src
        self._completed = False

    @property
    def name(self):
        return f'import/{self._python_module_src.name}'

    @property
    def ready(self):
        return False

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return []

    def update_status(self):
        pass

    def set_completed(self):
        self._completed = True


class ImportTarget:

    def __init__(self, python_module_src, type_src_list, alias, idx=1, req_to_target=None):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._alias = alias
        self._idx = idx
        self._req_to_target = req_to_target or {}
        self._completed = False
        self._ready = False

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

    def set_alias_completed(self):
        self._alias.set_completed()

    def create_next_target(self, req_to_target):
        return ImportTarget(self._python_module_src, self._type_src_list, self._alias, self._idx + 1, req_to_target)

    def create_test_target(self, function, req_to_target):
        return TestTarget(self._python_module_src, self._type_src_list, function, req_to_target)

    def get_resource_target(self, target_factory):
        return target_factory.python_module_resource_by_src(self._python_module_src)


def create_import_targets(target_set, python_module_src_list, type_src_list):
    import_targets = []
    for python_module_src in python_module_src_list:
        alias_tgt = ImportTargetAlias(python_module_src)
        import_tgt = ImportTarget(python_module_src, type_src_list, alias_tgt)
        import_targets.append(import_tgt)
        target_set.add(import_tgt)
        target_set.add(alias_tgt)
    all_imports_known = AllImportsKnownTarget(import_targets)
    target_set.add(all_imports_known)
