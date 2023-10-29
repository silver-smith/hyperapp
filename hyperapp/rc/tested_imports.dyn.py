from hyperapp.common.htypes import HException
from hyperapp.common.python_importer import Finder

from . import htypes


class TestedObject:

    def __init__(self, prefix):
        self._prefix = prefix

    @property
    def path(self):
        return self._prefix

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        resource_path = (*self._prefix, name)
        return TestedObject(resource_path)

    def __call__(self, *args, **kw):
        path = '.'.join(self._prefix)
        raise htypes.tested_imports.using_tested_object(f"Attempt to use tested object {path} with: *{args}, **{kw}")

    def __mro_entries__(self, base):
        path = '.'.join(self._prefix)
        raise htypes.tested_imports.using_tested_object(f"Attempt to inherit from tested class {path}")


class TestedImport(Finder):

    _is_package = True

    def __init__(self, piece):
        self._base_module_name = None

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
        return TestedObject(name)

    def exec_module(self, module):
        pass
