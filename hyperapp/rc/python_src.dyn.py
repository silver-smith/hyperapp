from dataclasses import dataclass
from pathlib import Path

from . import htypes
from .services import (
    mosaic,
    )


@dataclass
class PythonModuleSrc:

    name: str
    stem: str
    _full_path: str
    resource_path: Path
    _contents: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.name, piece.stem, piece.full_path, Path(piece.resource_path), piece.contents)

    @property
    def piece(self):
        return htypes.python_src.python_module_src(
            name=self.name,
            stem=self.stem,
            full_path=self._full_path,
            resource_path=str(self.resource_path),
            contents=self._contents,
            )

    def python_module(self, import_list):
        return htypes.builtin.python_module(
            module_name=self.stem,
            source=self._contents,
            file_path=self._full_path,
            import_list=tuple(import_list),
            )

    def recorded_python_module(self, tag):
        recorder = htypes.import_recorder.import_recorder(self.name, tag)
        recorder_import_list = [
            htypes.builtin.import_rec('*', mosaic.put(recorder)),
            ]
        python_module = self.python_module(recorder_import_list)
        return (recorder, python_module)
