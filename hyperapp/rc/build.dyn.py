import logging
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from . import htypes
from .services import (
    builtin_types,
    local_types,
    hyperapp_dir,
    mosaic,
    pyobj_creg,
    type_module_loader,
    )

log = logging.getLogger(__name__)


@dataclass
class PythonModuleSrc:

    name: str
    stem: str
    path: Path
    resource_path: Path
    contents: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.name, piece.stem, Path(piece.path), Path(piece.resource_path), piece.contents)

    @property
    def piece(self):
        return htypes.build.python_module_src(
            name=self.name,
            stem=self.stem,
            path=str(self.path),
            resource_path=str(self.resource_path),
            contents=self.contents,
            )

    def python_module(self, import_list):
        return htypes.builtin.python_module(
            module_name=self.stem,
            source=self.contents,
            file_path=str(hyperapp_dir / self.path),
            import_list=tuple(import_list),
            )

    def recorded_python_module(self, tag):
        recorder = htypes.import_recorder.import_recorder(self.name, tag)
        recorder_import_list = [
            htypes.builtin.import_rec('*', mosaic.put(recorder)),
            ]
        python_module = self.python_module(recorder_import_list)
        return (recorder, python_module)


class TypeSources:

    def __init__(self, type_src_list):
        self._type_src_list = type_src_list

    @property
    def as_list(self):
        return self._type_src_list

    def get(self, module_name, name):
        return self.as_dict.get(module_name, {}).get(name)

    def get_src(self, module_name, name):
        return self.as_src_dict.get(module_name, {}).get(name)

    # Make same format as local_types service.
    @cached_property
    def as_dict(self):
        custom_types = {}
        for src in self._type_src_list:
            name_to_type = custom_types.setdefault(src.module_name, {})
            name_to_type[src.name] = src.type_piece
        return custom_types

    @cached_property
    def as_src_dict(self):
        custom_types = {}
        for src in self._type_src_list:
            name_to_type = custom_types.setdefault(src.module_name, {})
            name_to_type[src.name] = src
        return custom_types


@dataclass
class TypeSrc:

    module_name: str
    name: str
    type_piece: Any

    @property
    def piece(self):
        return htypes.build.type_src(
            module_name=self.module_name,
            name=self.name,
            type=mosaic.put(self.type_piece),
            )


class Build:

    def __init__(self, types, python_modules, job_cache):
        self.types = types
        self.python_modules = python_modules
        self.job_cache = job_cache

    @property
    def piece(self):
        return htypes.build.full_build_task(
            types=tuple(self.types),
            python_modules=tuple(self.python_modules),
            )

    def report(self):
        for t in self.types.as_list:
            log.info("\tType: %s", t)
        for m in self.python_modules:
            log.info("\tPython module: %s", m)


def _load_pyhon_modules(root_dir):
    for path in root_dir.rglob('*.dyn.py'):
        rel_path = path.relative_to(root_dir)
        if 'test' in rel_path.parts:
            continue
        stem = path.name[:-len('.dyn.py')]
        dir = path.parent.relative_to(root_dir)
        dir_name = str(dir).replace('/', '.')
        name = f'{dir_name}.{stem}'
        resource_path = rel_path.with_name(stem + '.resources.yaml')
        yield PythonModuleSrc(name, stem, rel_path, resource_path, path.read_text())


def _load_types(root_dir):
    types = local_types.copy()
    for name, t in builtin_types.items():
        type_piece = pyobj_creg.actor_to_piece(t)
        yield TypeSrc('builtin', name, type_piece)
    type_module_loader.load_type_modules([root_dir], types)
    for module_name, name_to_type in types.items():
        for name, type_piece in name_to_type.items():
            yield TypeSrc(module_name, name, type_piece)


def load_build(root_dir, job_cache):
    return Build(
        types=TypeSources(list(_load_types(root_dir))),
        python_modules=list(_load_pyhon_modules(root_dir)),
        job_cache=job_cache,
        )
