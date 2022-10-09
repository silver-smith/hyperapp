import importlib.util
from types import ModuleType

from hyperapp.common.python_importer import Finder

from .services import (
    python_object_creg,
    )


class _ServicesModule(ModuleType):

    def __init__(self, name, resources, import_set):
        super().__init__(name)
        self._resources = resources
        self._import_set = import_set

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        try:
            resource_ref = self._resources[f'services.{name}']
        except KeyError:
            raise RuntimeError(f"Unknown service: {name!r}")
        try:
            service = python_object_creg.invite(resource_ref)
        except Exception as x:
            raise RuntimeError(f"Error importing service {name!r}: {x}")
        self._import_set.add(f'services.{name}')
        return service


class _HTypesModule(ModuleType):

    def __init__(self, name, resources, import_set, type_module_name):
        super().__init__(name)
        self._resources = resources
        self._import_set = import_set
        self._type_module_name = type_module_name

    def __getattr__(self, name):
        full_name = f'{self._type_module_name}.{name}'
        self._import_set.add(f'htypes.{full_name}')
        try:
            resource_ref = self._resources[f'htypes.{full_name}']
        except KeyError:
            raise RuntimeError(f"Unknown htype: {full_name!r}")
        try:
            return python_object_creg.invite(resource_ref)
        except Exception as x:
            raise RuntimeError(f"Error importing htype {full_name!r}: {x}")


class _HTypesRoot(ModuleType):

    def __init__(self, name, resources, import_set):
        super().__init__(name)
        self._resources = resources
        self._import_set = import_set

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        module = _HTypesModule(f'{self.__name__}.{name}', self._resources, self._import_set, name)
        module.__name__ = f'{self.__name__}.{name}'
        module.__loader__ = self.__loader__
        module.__path__ = None
        module.__package__ = self
        module.__spec__ = None
        module.__file__ = None
        return module


class _CodeModule(ModuleType):

    def __init__(self, code_module):
        super().__init__()
        self.code_module = code_module


class AutoImporter(Finder):

    _is_package = True

    def __init__(self, piece):
        self._import_set = set()
        self._base_module_name = None
        self._resources = {
            r.name: r.resource
            for r in piece.resources
            }

    def imports(self):
        return list(sorted(self._import_set))

    def set_base_module_name(self, name):
        self._base_module_name = name

    # Finder interface:

    def get_spec(self, fullname):
        spec = super().get_spec(fullname)
        return spec

    def create_module(self, spec):
        # module = importlib.util.module_from_spec(spec)
        # return module
        assert spec.name.startswith(self._base_module_name + '.')
        rel_name = spec.name[len(self._base_module_name) + 1 :]
        last_name = spec.name.split('.')[-1]
        if rel_name == 'services':
            module = _ServicesModule(spec.name, self._resources, self._import_set)
        elif rel_name == 'htypes':
            module = _HTypesRoot(spec.name, self._resources, self._import_set)
        elif rel_name.startswith('htypes.'):
            root =_HTypesRoot(spec.name, self._resources, self._import_set)
            module = getattr(root, last_name)
        else:
            if '.' in rel_name:
                raise RuntimeError(f"Unsupported import style: {rel_name}")
            module = self._import_sub_module(spec, last_name)
        module.__name__ = spec.name
        module.__loader__ = self
        module.__path__ = None
        module.__package__ = spec.parent
        return module

    def exec_module(self, module):
        pass

    def _import_sub_module(self, spec, module_name):
        try:
            resource_res = self._resources[module_name]
        except KeyError:
            raise RuntimeError(f"Unknown code module: {module_name}")
        python_module = python_object_creg.invite(resource_res)
        module = ModuleType(spec.name)
        module.__dict__.update(python_module.__dict__)
        self._import_set.add(module_name)
        return module
