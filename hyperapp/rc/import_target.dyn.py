from . import htypes
from .services import (
    rc_requirement_creg,
    )
from .code.rc_constants import JobStatus
from .code.job_result import JobResult
from .code.import_resource import ImportResource
from .code.import_job import ImportJob


class ImportTarget:

    def __init__(self, python_module_src, type_src_list, idx=1, req_to_target=None):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._idx = idx
        self._req_to_target = req_to_target or {}
        self._key = ('import_target', self._python_module_src.name, self._idx)
        self._completed = False
        self._ready = False
        self.update_status()

    def __eq__(self, rhs):
        return type(rhs) is ImportTarget and self._key == rhs._key

    def __hash__(self):
        return hash(self._key)

    @property
    def name(self):
        return f'import/{self._python_module_src.name}/{self._idx}'

    @property
    def ready(self):
        return self._ready

    @property
    def completed(self):
        return self._completed

    def update_status(self):
        self._ready = all(target.completed for target in self._req_to_target.values())

    def make_job(self):
        resources = [
            ImportResource.from_type_src(src)
            for src in self._type_src_list
            ]
        return ImportJob(self._python_module_src, self._idx, resources)

    def handle_job_result(self, target_set, result):
        req_to_target = {}
        for req_ref in result.requirements:
            req = rc_requirement_creg.invite(req_ref)
            target = req.get_target(target_set.factory)
            req_to_target[req] = target
        self._completed = True
        if isinstance(result, htypes.import_job.error_result):
            return JobResult(JobStatus.failed, result.message, result.traceback)
        elif isinstance(result, htypes.import_job.incomplete_result):
            if req_to_target:  # TODO: remove after all requirement types are implemented.
                target_set.add(ImportTarget(self._python_module_src, self._type_src_list, self._idx + 1, req_to_target))
            return JobResult(JobStatus.incomplete, result.message, result.traceback)
        return JobResult(JobStatus.ok)
