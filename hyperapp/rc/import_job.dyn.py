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
from .code.build import PythonModuleSrc
from .code.import_recorder import IncompleteImportedObjectError


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
        recorder_resources = tuple(
            htypes.import_recorder.resource(
                name=tuple(rec.full_name.split('.')),
                resource=rec.resource,
                )
            for rec in import_list
            )
        recorder = htypes.import_recorder.import_recorder(
            id=src.name,
            resources=recorder_resources,
        )
        recorder_import_list = [
            htypes.builtin.import_rec('*', mosaic.put(recorder)),
            ]
        module_piece = htypes.builtin.python_module(
            module_name=src.name,
            source=src.contents,
            file_path=str(hyperapp_dir / src.path),
            import_list=tuple(recorder_import_list),
            )
        try:
            module = pyobj_creg.animate(module_piece)
        except PythonModuleResourceImportError as x:
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
                return htypes.import_job.incomplete_result(
                    message=str(x),
                    traceback=tuple(traceback_lines[:-1]),
                    )
            else:
                return htypes.import_job.error_result(
                    message=str(x),
                    traceback=tuple(traceback_lines),
                    )
