import importlib.util
from types import ModuleType

from hyperapp.common.python_importer import Finder

from . import htypes
from .services import (
    builtin_services,
    local_modules,
    local_types,
    mosaic,
    python_object_creg,
    resource_module_registry,
    types,
    services,
    )


class _ServicesModule(ModuleType):

    def __init__(self, name, import_dict):
        super().__init__(name)
        self._import_dict = import_dict
        self._requirement_to_module = {
            service_name: local_modules.by_name[module_name]
            for module_name, service_name_set in local_modules.module_provides.items()
            for service_name in service_name_set
            }
        self._resource_to_module = {
            name: res_module
            for module_name, res_module in resource_module_registry.items()
            for name in res_module
            if not module_name.startswith('legacy_')
            }

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name in builtin_services:
            service = self._pick_legacy_service(name)
            resource_name = f'legacy_service.{name}'
        elif name in self._requirement_to_module:
            self._load_legacy_code_module(self._requirement_to_module[name], name)
            service = self._pick_legacy_service(name)
            resource_name = f'legacy_service.{name}'
        else:
            try:
                res_module = self._resource_to_module[name]
            except KeyError:
                raise RuntimeError(f"Unknown service: {name!r}")
            service = self._load_resource(res_module, name)
            resource_name = f'{res_module.name}.{name}'
        self._import_dict[f'services.{name}'] = resource_name
        return service

    def _pick_legacy_service(self, name):
        try:
            return getattr(services, name)
        except AttributeError:
            # Allowing AttributeError leaving __getattr__ leads to undesired behaviour.
            raise RuntimeError(f"Error retrieving service: {name!r}")

    def _load_legacy_code_module(self, code_module, name):
        code_module_ref = mosaic.put(code_module)
        try:
            _ = python_object_creg.invite(code_module_ref)  # Ensure it is loaded.
        except Exception as x:
            # Should convert exception or it will be swallowed.
            raise RuntimeError(f"Error importing module {code_module.module_name} for service {name!r}: {x}")

    def _load_resource(self, res_module, name):
        try:
            resource = res_module[name]
            return python_object_creg.animate(resource)
        except Exception as x:
            # Should convert exception or it will be swallowed.
            raise RuntimeError(f"Error resolving service from resource {res_module.name}.{name}: {x}")


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
        if name.startswith('_'):
            raise AttributeError(name)
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


class AutoImporter(Finder):

    _is_package = True

    def __init__(self):
        self._import_dict = {}
        self._base_module_name = None

    def imports(self):
        return [
            htypes.auto_importer.import_rec(key, value)
            for key, value in sorted(self._import_dict.items())
            ]

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
            module = _ServicesModule(spec.name, self._import_dict)
        elif rel_name == 'htypes':
            module = _HTypesRoot(spec.name, self._import_dict)
        elif rel_name.startswith('htypes.'):
            root =_HTypesRoot(spec.name, self._import_dict)
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
        for name in local_modules.by_name:
            package_name, name = name.rsplit('.', 1)
            if name == module_name:
                break
        else:
            raise RuntimeError(f"Unknown code module: {module_name}")
        module_res = resource_module_registry[f'legacy_module.{package_name}']
        python_module = python_object_creg.animate(module_res[name])
        module = ModuleType(spec.name)
        module.__dict__.update(python_module.__dict__)
        self._import_dict[module_name] = f'legacy_module.{package_name}.{name}'
        return module
