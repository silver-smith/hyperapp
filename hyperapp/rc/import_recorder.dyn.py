from hyperapp.common.python_importer import Finder

from .services import (
    pyobj_creg,
    web,
    )


class IncompleteImportedObjectError(Exception):
    pass


def _load_resource(resource_path, resource):
    try:
        return pyobj_creg.animate(resource)
    except Exception as x:
        raise RuntimeError(f"Error importing {'.'.join(resource_path)!r}: {x}") from x


def _get_resource(resource_path, resources, packages, imported_set):
    imported_set.add(resource_path)
    try:
        resource = resources[resource_path]
    except KeyError:
        return RecorderObject(resource_path, resources, packages, imported_set)
    else:
        return _load_resource(resource_path, resource)


class RecorderObject:

    def __init__(self, prefix, resources, packages, imported_set):
        self._prefix = prefix
        self._resources = resources
        self._packages = packages
        self._imported_set = imported_set

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        resource_path = (*self._prefix, name)
        return _get_resource(resource_path, self._resources, self._packages, self._imported_set)

    def __call__(self, *args, **kw):
        path = '.'.join(self._prefix)
        raise IncompleteImportedObjectError(f"Attempt to use not-ready object {path} with: *{args}, **{kw}")

    def __mro_entries__(self, base):
        path = '.'.join(self._prefix)
        raise IncompleteImportedObjectError(f"Attempt to inherit from not-ready class {path}")


class ImportRecorder(Finder):

    _is_package = True

    @classmethod
    def from_piece(cls, piece):
        resources = {
            rec.name: web.summon(rec.resource)
            for rec in piece.resources
            }
        return cls(resources)

    def __init__(self, resources):
        self._resources = resources  # name tuple -> resource piece.
        self._packages = self._collect_packages()  # name tuple set.
        self._imported_set = set()  # name tuple set.
        self._base_module_name = None

    def _collect_packages(self):
        packages = set()
        for name in self._resources.keys():
            for i in range(1, len(name)):
                prefix = name[:i]
                if prefix not in self._resources:
                    packages.add(prefix)
        return packages

    @property
    def used_imports(self):
        return self._imported_set

    # Called by python importer.
    def set_base_module_name(self, name):
        self._base_module_name = name

    def create_module(self, spec):
        assert spec.name.startswith(self._base_module_name + '.')
        rel_name = spec.name[len(self._base_module_name) + 1 :]
        resource_path = tuple(rel_name.split('.'))
        return _get_resource(resource_path, self._resources, self._packages, self._imported_set)
