import importlib.util
import types

from hyperapp.common.python_importer import Finder

from . import htypes


class _ServicesModule(types.ModuleType):

    def __init__(self, name, services, import_dict):
        super().__init__(name)
        self._services = services
        self._import_dict = import_dict

    def __getattr__(self, name):
        try:
            service = getattr(self._services, name)
        except AttributeError:
            raise RuntimeError(f"Unknown service: {name!r}")
        self._import_dict[f'services.{name}'] = f'legacy_service.{name}'
        return service


class _HTypesModule(types.ModuleType):

    def __init__(self, name, import_dict, types, type_module_name, type_module):
        super().__init__(name)
        self._import_dict = import_dict
        self._types = types
        self._type_module_name = type_module_name
        self._type_module = type_module

    def __getattr__(self, name):
        full_name = f'{self._type_module_name}.{name}'
        self._import_dict[f'htypes.{full_name}'] = f'legacy_type.{full_name}'
        try:
            type_ref = self._type_module[name]
        except KeyError:
            raise RuntimeError(f"Unknown type: {full_name}")
        return self._types.resolve(type_ref)


class _HTypesRoot(types.ModuleType):

    def __init__(self, name, import_dict, types, local_type_module_reg):
        super().__init__(name)
        self._import_dict = import_dict
        self._types = types
        self._local_type_module_reg = local_type_module_reg

    def __getattr__(self, name):
        try:
            type_module = self._local_type_module_reg[name]
        except KeyError:
            raise RuntimeError(f"Unknown type module: {name}")
        module = _HTypesModule(f'{self.__name__}.{name}', self._import_dict, self._types, name, type_module)
        module.__name__ = f'{self.__name__}.{name}'
        module.__loader__ = self.__loader__
        module.__path__ = None
        module.__package__ = self
        module.__spec__ = None
        module.__file__ = None
        return module


class _CodeModule(types.ModuleType):

    def __init__(self, code_module):
        super().__init__()
        self.code_module = code_module


class _Loader(Finder):

    _is_package = True

    def __init__(self, services, types, local_type_module_reg, code_module_dict, import_dict):
        self._services = services
        self._types = types
        self._local_type_module_reg = local_type_module_reg
        self._code_module_dict = code_module_dict
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
            module = _ServicesModule(spec.name, self._services, self._import_dict)
        elif rel_name == 'htypes':
            module = _HTypesRoot(spec.name, self._import_dict, self._types, self._local_type_module_reg)
        elif rel_name.startswith('htypes.'):
            root =_HTypesRoot(spec.name, self._import_dict, self._types, self._local_type_module_reg)
            module = getattr(root, last_name)
        else:
            for name, code_module in self._code_module_dict.items():
                if name.split('.')[-1] == last_name:
                    break
            else:
                raise RuntimeError(f"Unknown code module: {last_name}")
            module = types.ModuleType(spec.name)
            module.__dict__.update(code_module.__dict__)
            self._import_dict[rel_name] = f'legacy_module.{name}'
        module.__name__ = spec.name
        module.__loader__ = self
        module.__path__ = None
        module.__package__ = spec.parent
        return module

    def exec_module(self, module):
        pass


class AutoImporter:

    def __init__(self, services, types, type_module_loader, module_registry):
        self._services = services
        self._types = types
        self._local_type_module_reg = type_module_loader.registry
        self._code_module_dict = {
            rec.name: rec.python_module
            for rec in module_registry.elements()
            }
        self._import_dict = {}

    def loader(self):
        return _Loader(self._services, self._types, self._local_type_module_reg, self._code_module_dict, self._import_dict)

    def imports(self):
        return [
            htypes.auto_importer.import_rec(key, value)
            for key, value in sorted(self._import_dict.items())
            ]
