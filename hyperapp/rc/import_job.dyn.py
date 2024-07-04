from . import htypes
from .code.build import PythonModuleSrc


class ImportJob:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            python_module_src=PythonModuleSrc.from_piece(piece.python_module),
            idx=piece.idx,
            )

    def __init__(self, python_module_src, idx):
        self._python_module_src = python_module_src
        self._idx = idx

    def __repr__(self):
        return f"<ImportJob {self._python_module_src}/{self._idx}>"

    @property
    def piece(self):
        return htypes.import_job.job(
            python_module=self._python_module_src.piece,
            idx=self._idx,
            )
