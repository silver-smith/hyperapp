import traceback

from hyperapp.common.util import flatten
from hyperapp.resource.python_module import PythonModuleResourceImportError

from . import htypes
from .services import (
    mosaic,
    hyperapp_dir,
    pyobj_creg,
    rc_dep_creg,
    )
from .code.rc_constants import JobStatus
from .code.build import PythonModuleSrc
from .code.import_recorder import IncompleteImportedObjectError
from .code.requirement_factory import RequirementFactory


class ImportJob:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            deps=[rc_dep_creg.invite(d) for d in piece.deps],
            )

    def __init__(self, python_module_src, idx, deps):
        self._python_module_src = python_module_src
        self._idx = idx
        self._deps = deps

    def __repr__(self):
        return f"<ImportJob {self._python_module_src}/{self._idx}>"

    @property
    def piece(self):
        return htypes.import_job.job(
            python_module=self._python_module_src.piece,
            idx=self._idx,
            deps=tuple(mosaic.put(d.piece) for d in self._deps),
            )

    def run(self):
        src = self._python_module_src
        import_list = flatten(d.import_records for d in self._deps)
        recorder, recorder_import_list = self._wrap_in_recorder(src, import_list)
        module_piece = htypes.builtin.python_module(
            module_name=src.name,
            source=src.contents,
            file_path=str(hyperapp_dir / src.path),
            import_list=tuple(recorder_import_list),
            )
        try:
            module = pyobj_creg.animate(module_piece)
            status = JobStatus.ok
        except PythonModuleResourceImportError as x:
            status, error_msg, traceback = self._prepare_error(x)
        if status == JobStatus.failed:
            return htypes.import_job.error_result(error_msg, traceback)
        req_set = self._imports_to_requirements(recorder.used_imports)
        if status == JobStatus.incomplete:
            req_refs = tuple(
                mosaic.put(req.piece)
                for req in req_set
                )
            return htypes.import_job.incomplete_result(
                requirements=req_refs,
                message=error_msg,
                traceback=tuple(traceback),
                )

    def _wrap_in_recorder(self, src, import_list):
        recorder_resources = tuple(
            htypes.import_recorder.resource(
                name=tuple(rec.full_name.split('.')),
                resource=rec.resource,
                )
            for rec in import_list
            )
        recorder_piece = htypes.import_recorder.import_recorder(
            id=src.name,
            resources=recorder_resources,
        )
        recorder_import_list = [
            htypes.builtin.import_rec('*', mosaic.put(recorder_piece)),
            ]
        recorder = pyobj_creg.animate(recorder_piece)
        return (recorder, recorder_import_list)

    def _prepare_error(self, x):
        traceback_entries = []
        cause = x.original_error
        while cause:
            traceback_entries += traceback.extract_tb(cause.__traceback__)
            cause = cause.__cause__
        for idx, entry in enumerate(traceback_entries):
            if entry.name == 'exec_module':
                del traceback_entries[:idx + 1]
                break
        traceback_lines = traceback.format_list(traceback_entries)
        if isinstance(x.original_error, IncompleteImportedObjectError):
            return (JobStatus.incomplete, str(x), traceback_lines[:-1])
        else:
            return (JobStatus.failed, str(x), traceback_lines)

    def _imports_to_requirements(self, import_set):
        # print("Used imports", import_set)
        req_set = set()
        for import_path in import_set:
            req = RequirementFactory().requirement_from_import(import_path)
            if req:
                req_set.add(req)
        return req_set
