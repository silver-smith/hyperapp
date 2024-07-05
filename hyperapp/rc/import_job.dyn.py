import traceback

from hyperapp.common.util import flatten

from . import htypes
from .services import (
    mosaic,
    hyperapp_dir,
    pyobj_creg,
    rc_dep_creg,
    )
from .code.build import PythonModuleSrc


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
        module_piece = htypes.builtin.python_module(
            module_name=src.name,
            source=src.contents,
            file_path=str(hyperapp_dir / src.path),
            import_list=tuple(import_list),
            )
        try:
            module = pyobj_creg.animate(module_piece)
        except Exception as x:
            traceback_entries = tuple(traceback.format_tb(x.__traceback__))
            return htypes.import_job.error_result(
                message=str(x),
                traceback=traceback_entries,
                )
