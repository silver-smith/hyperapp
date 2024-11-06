import logging

from hyperapp.common.python_importer import Finder

log = logging.getLogger(__name__)

from .services import (
    pyobj_creg,
    web,
    )


class IncompleteImportedObjectError(Exception):

    def __init__(self, path, msg):
        super().__init__(msg)
        self.path = path


class _ImportsCollector:

    def __init__(self, resources, packages, missing_imports, used_imports):
        self._resources = resources  # name tuple -> resource piece.
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
            resource = self._resources[resource_path]
        except KeyError:
            self._missing_imports.add(resource_path)
            return RecorderObject(resource_path, self._resources, self._packages, self._missing_imports, self._used_imports)
        else:
            self._used_imports.add(resource_path)
            return self._load_resource(resource_path, resource)


class RecorderObject(_ImportsCollector):

    def __init__(self, prefix, resources, packages, missing_imports, used_imports):
        super().__init__(resources, packages, missing_imports, used_imports)
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
    def from_piece(cls, piece):
        resources = {
            rec.name: web.summon(rec.resource)
            for rec in piece.resources
            }
        return cls(resources)

    def __init__(self, resources):
        _ImportsCollector.__init__(
            self,
            resources=resources,
            packages=self._collect_packages(resources),
            missing_imports=set(),
            used_imports=set(),
            )
        self._base_module_name = None

    @staticmethod
    def _collect_packages(resources):
        packages = set()
        for name in resources.keys():
            for i in range(1, len(name)):
                prefix = name[:i]
                if prefix not in resources:
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
