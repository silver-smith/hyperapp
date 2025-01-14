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
    path: Path
    full_path: str
    resource_path: Path
    contents: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.name, piece.stem, Path(piece.path), piece.full_path, Path(piece.resource_path), piece.contents)

    @property
    def piece(self):
        return htypes.python_src.python_module_src(
            name=self.name,
            stem=self.stem,
            path=str(self.path),
            full_path=self.full_path,
            resource_path=str(self.resource_path),
            contents=self.contents,
            )

    def python_module(self, import_list):
        return htypes.builtin.python_module(
            module_name=self.stem,
            source=self.contents,
            file_path=self.full_path,
            import_list=tuple(import_list),
            )

    def recorded_python_module(self, tag):
        recorder = htypes.import_recorder.import_recorder(self.name, tag)
        recorder_import_list = [
            htypes.builtin.import_rec('*', mosaic.put(recorder)),
            ]
        python_module = self.python_module(recorder_import_list)
        return (recorder, python_module)
