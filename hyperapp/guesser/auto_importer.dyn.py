import importlib.util
from types import ModuleType

from hyperapp.common.python_importer import Finder

from . import htypes
from .services import (
    builtin_services,
    local_modules,
    local_types,
    python_object_creg,
    resource_module_registry,
    types,
    services,
    )


class _ServicesModule(ModuleType):

    def __init__(self, name, import_dict):
        super().__init__(name)
        self._import_dict = import_dict

    def __getattr__(self, name):
        try:
            service = getattr(services, name)
        except AttributeError:
            raise RuntimeError(f"Unknown service: {name!r}")
        self._import_dict[f'services.{name}'] = f'legacy_service.{name}'
        return service


class _HTypesModule(ModuleType):

    def __init__(self, name, import_dict, type_module_name, type_module):
        super().__init__(name)
        self._import_dict = import_dict
        self._type_module_name = type_module_name
        self._type_module = type_module

    def __getattr__(self, name):
        full_name = f'{self._type_module_name}.{name}'
        self._import_dict[f'htypes.{full_name}'] = f'legacy_type.{full_name}'
        try:
            type_ref = self._type_module[name]
        except KeyError:
            raise RuntimeError(f"Unknown type: {full_name}")
        return types.resolve(type_ref)


class _HTypesRoot(ModuleType):

    def __init__(self, name, import_dict):
        super().__init__(name)
        self._import_dict = import_dict

    def __getattr__(self, name):
        try:
            type_module = local_types[name]
        except KeyError:
            raise RuntimeError(f"Unknown type module: {name}")
        module = _HTypesModule(f'{self.__name__}.{name}', self._import_dict, name, type_module)
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


class _Loader(Finder):

    _is_package = True

    def __init__(self, import_dict):
        self._import_dict = import_dict
        self._base_module_name = None

    def set_base_module_name(self, name):
        self._base_module_name = name

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
            module = _ServicesModule(spec.name, self._import_dict)
        elif rel_name == 'htypes':
            module = _HTypesRoot(spec.name, self._import_dict)
        elif rel_name.startswith('htypes.'):
            root =_HTypesRoot(spec.name, self._import_dict)
            module = getattr(root, last_name)
        else:
            for name in local_modules.by_name:
                package_name, name = name.rsplit('.', 1)
                if name == last_name:
                    break
            else:
                raise RuntimeError(f"Unknown code module: {last_name}")
            module_res = resource_module_registry[f'legacy_module.{package_name}']
            python_module = python_object_creg.animate(module_res[name])
            module = ModuleType(spec.name)
            module.__dict__.update(python_module.__dict__)
            self._import_dict[rel_name] = f'legacy_module.{package_name}.{name}'
        module.__name__ = spec.name
        module.__loader__ = self
        module.__path__ = None
        module.__package__ = spec.parent
        return module

    def exec_module(self, module):
        pass


class AutoImporter:

    def __init__(self):
        self._import_dict = {}

    def loader(self):
        return _Loader(self._import_dict)

    def imports(self):
        return [
            htypes.auto_importer.import_rec(key, value)
            for key, value in sorted(self._import_dict.items())
            ]
