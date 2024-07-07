from . import htypes
from .services import (
    rc_requirement_creg,
    )
from .code.rc_constants import JobStatus
from .code.job_result import JobResult
from .code.import_dep import ImportDep
from .code.import_job import ImportJob


class ImportTarget:

    def __init__(self, python_module_src, type_src_list, idx=1):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._idx = idx
        self._key = ('import_target', self._python_module_src.name, self._idx)
        self._completed = False

    def __eq__(self, rhs):
        return type(rhs) is ImportTarget and self._key == rhs._key

    def __hash__(self):
        return hash(self._key)

    @property
    def name(self):
        return f'import/{self._python_module_src.name}/{self._idx}'

    @property
    def ready(self):
        return True

    @property
    def completed(self):
        return self._completed

    def make_job(self):
        deps = [
            ImportDep.from_type_src(src)
            for src in self._type_src_list
            ]
        return ImportJob(self._python_module_src, self._idx, deps)

    def handle_job_result(self, target_set, result):
        requirements = set()
        for req_ref in result.requirements:
            requirements.add(rc_requirement_creg.invite(req_ref))
        self._completed = True
        if isinstance(result, htypes.import_job.error_result):
            return JobResult(JobStatus.failed, result.message, result.traceback)
        elif isinstance(result, htypes.import_job.incomplete_result):
            return JobResult(JobStatus.incomplete, result.message, result.traceback)
        return JobResult(JobStatus.ok)
