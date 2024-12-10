import logging

from hyperapp.common.python_importer import Finder

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

    def __init__(self, module_name, config, packages, missing_imports, used_imports):
        self._module_name = module_name
        self._config = config  # (module name, import name (tuple)) -> resource piece.
        self._packages = packages  # name tuple set.
        self._missing_imports = missing_imports  # name tuple set.
        self._used_imports = used_imports  # name tuple set.

    @staticmethod
    def _load_resource(resource_path, resource):
        try:
            return pyobj_creg.animate(resource)
        except Exception as x:
            raise RuntimeError(f"Error importing {'.'.join(resource_path)!r}: {x}") from x

    def _get_resource(self, resource_path):
        try:
            resource = self._config[self._module_name, resource_path]
        except KeyError:
            try:
                resource = self._config['', resource_path]
            except KeyError:
                self._missing_imports.add(resource_path)
                return RecorderObject(self._module_name, resource_path, self._config, self._packages, self._missing_imports, self._used_imports)
        self._used_imports.add(resource_path)
        return self._load_resource(resource_path, resource)


class RecorderObject(_ImportsCollector):

    def __init__(self, module_name, prefix, config, packages, missing_imports, used_imports):
        super().__init__(module_name, config, packages, missing_imports, used_imports)
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
    def from_piece(cls, piece, import_recorder_reg):
        assert import_recorder_reg, import_recorder_reg
        import_names = {
            import_name
            for (module_name, import_name) in import_recorder_reg
            if not module_name or module_name == piece.module_name
            }
        packages = cls._collect_packages(import_names)
        return cls(piece.module_name, import_recorder_reg, packages)

    def __init__(self, module_name, config, packages):
        _ImportsCollector.__init__(
            self,
            module_name=module_name,
            config=config,
            packages=packages,
            missing_imports=set(),
            used_imports=set(),
            )
        self._base_module_name = None

    @staticmethod
    def _collect_packages(import_names):
        packages = set()
        for name in import_names:
            for i in range(1, len(name)):
                prefix = name[:i]
                if prefix not in import_names:
                    packages.add(prefix)
        return packages

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
        assert spec.name.startswith(self._base_module_name + '.')
        rel_name = spec.name[len(self._base_module_name) + 1 :]
        resource_path = tuple(rel_name.split('.'))
        return self._get_resource(resource_path)


def import_recorder_reg(config):
    return config
