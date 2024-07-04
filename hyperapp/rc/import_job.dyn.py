from . import htypes
from .services import (
    mosaic,
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
