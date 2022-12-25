from hyperapp.common.python_importer import Finder

from .services import (
    python_object_creg,
    )


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
        resource_path_str = '.'.join(resource_path)
        if resource_path in self._packages:
            return RecorderObject(resource_path, self._resources, self._packages, self._imported_set)
        try:
            resource_ref = self._resources[resource_path]
        except KeyError:
            raise RuntimeError(f"Unknown name for import: {resource_path_str!r}")
        try:
            object = python_object_creg.invite(resource_ref)
        except Exception as x:
            raise RuntimeError(f"Error importing {resource_path_str!r}: {x}")
        self._imported_set.add(resource_path)
        return object


class ImportRecorder(Finder):

    _is_package = True

    def __init__(self, piece):
        self._base_module_name = None
        self._resources = {
            r.name: r.resource
            for r in piece.resources
            }
        self._packages = set()
        for name in self._resources.keys():
            for i in range(1, len(name)):
                prefix = name[:i]
                if prefix not in self._resources:
                    self._packages.add(prefix)
        self._imported_set = set()

    def reset(self):
        self._imported_set.clear()

    def used_imports(self):
        return list(sorted(self._imported_set))

    def set_base_module_name(self, name):
        self._base_module_name = name

    # Finder interface:

    def get_spec(self, fullname):
        spec = super().get_spec(fullname)
        return spec

    def create_module(self, spec):
        assert spec.name.startswith(self._base_module_name + '.')
        rel_name = spec.name[len(self._base_module_name) + 1 :]
        name = rel_name.split('.')
        return RecorderObject(name, self._resources, self._packages, self._imported_set)

    def exec_module(self, module):
        pass
