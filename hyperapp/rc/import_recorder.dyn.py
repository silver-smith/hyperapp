import logging

from hyperapp.boot.python_importer import Finder

log = logging.getLogger(__name__)

from . import htypes
from .services import (
    pyobj_creg,
    )


class IncompleteImportedObjectError(Exception):

    def __init__(self, path, msg):
        super().__init__(msg)
        self.path = path


class _ImportsCollector:

    def __init__(self, module_name, config, missing_imports, used_imports):
        self._module_name = module_name
        self._config = config  # (module name, import name (tuple)) -> resource piece.
        self._missing_imports = missing_imports  # name tuple set.
        self._used_imports = used_imports  # name tuple set.

    @staticmethod
    def _load_resource(resource_path, resource):
        try:
            return pyobj_creg.animate(resource)
        except Exception as x:
            raise RuntimeError(f"Error importing {'.'.join(resource_path)!r}: {x}") from x

    def _resolve_resource(self, resource_path):
        try:
            return self._config[self._module_name, resource_path]
        except KeyError:
            pass
        return self._config['', resource_path]

    def _get_resource(self, resource_path):
        try:
            resource = self._resolve_resource(resource_path)
        except KeyError:
            self._missing_imports.add(resource_path)
            return RecorderObject(self._module_name, resource_path, self._config, self._missing_imports, self._used_imports)
        self._used_imports.add(resource_path)
        return self._load_resource(resource_path, resource)


class RecorderObject(_ImportsCollector):

    def __init__(self, module_name, prefix, config, missing_imports, used_imports):
        super().__init__(module_name, config, missing_imports, used_imports)
        self._prefix = prefix

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        resource_path = (*self._prefix, name)
        return self._get_resource(resource_path)

    def __call__(self, *args, **kw):
        path = '.'.join(self._prefix)
        raise IncompleteImportedObjectError(self._prefix, f"Attempt to use not-ready object {path} with: *{args}, **{kw}")

    def __mro_entries__(self, base):
        path = '.'.join(self._prefix)
        raise IncompleteImportedObjectError(self._prefix, f"Attempt to inherit from not-ready class {path}")

    # RecorderObject may be using in type declaration during import stage, like 'AType|None', where AType is RecorderObject.
    def __or__(self, other_type):
        return self


class ImportRecorder(Finder, _ImportsCollector):

    _is_package = True

    @classmethod
    def from_piece(cls, piece, system, import_recorder_reg):
        return cls(piece.module_name, system, import_recorder_reg)

    def __init__(self, module_name, system_probe, config):
        _ImportsCollector.__init__(
            self,
            module_name=module_name,
            config=config,
            missing_imports=set(),
            used_imports=set(),
            )
        self._base_module_name = None
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._config = system_probe['import_recorder_reg']
        assert self._config.items()
        self._missing_imports.clear()
        self._used_imports.clear()

    @property
    def missing_imports(self):
        log.info("Recorder: Missing imports: %s", self._missing_imports)
        return self._missing_imports

    @property
    def used_imports(self):
        log.info("Recorder: Used imports: %s", self._used_imports)
        return self._used_imports

    # Called by python importer.
    def set_base_module_name(self, name):
        self._base_module_name = name

    def create_module(self, spec):
        assert self._config.items()
        assert spec.name.startswith(self._base_module_name + '.')
        rel_name = spec.name[len(self._base_module_name) + 1 :]
        resource_path = tuple(rel_name.split('.'))
        return self._get_resource(resource_path)


def import_recorder_reg(config):
    return config
