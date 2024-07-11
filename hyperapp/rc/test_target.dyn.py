from .code.import_resource import ImportResource
from .code.test_job import TestJob


class TestTarget:

    def __init__(self, python_module_src, type_src_list, function, req_to_target, idx=1):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._function = function
        self._req_to_target = req_to_target or {}
        self._idx = idx
        self._completed = False
        self._ready = False

    def __repr__(self):
        return f"<TestTarget {self.name}>"

    @property
    def name(self):
        return f'test/{self._python_module_src.name}/{self._function.name}/{self._idx}'

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
        resources = list(self._enum_resources())
        return TestJob(self._python_module_src, self._idx, resources, self._function.name)

    def _enum_resources(self):
        for src in self._type_src_list:
            yield ImportResource.from_type_src(src)
        for req, target in self._req_to_target.items():
            yield req.make_resource(target)

    def handle_job_result(self, target_set, result):
        self._completed = True
