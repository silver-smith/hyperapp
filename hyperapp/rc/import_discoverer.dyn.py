from hyperapp.common.htypes import HException
from hyperapp.common.python_importer import Finder

from . import htypes
from .services import (
    pyobj_creg,
)


class DiscovererObject:

    def __init__(self, prefix, imported_set):
        self._prefix = prefix
        self._imported_set = imported_set

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        resource_path = (*self._prefix, name)
        self._imported_set.add(resource_path)
        return DiscovererObject(resource_path, self._imported_set)

    def __call__(self, *args, **kw):
        path = '.'.join(self._prefix)
        raise htypes.import_discoverer.using_incomplete_object(f"Attempt to use not-ready object {path} with: *{args}, **{kw}")


class ImportDiscoverer(Finder):

    _is_package = True

    def __init__(self, piece):
        self._base_module_name = None
        self._imported_set = set()

    def reset(self):
        self._imported_set.clear()

    def discovered_imports(self):
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
        name = tuple(rel_name.split('.'))
        self._imported_set.add(name)
        return DiscovererObject(name, self._imported_set)

    def exec_module(self, module):
        pass
