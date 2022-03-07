import logging
import yaml
from collections import namedtuple
from functools import cached_property

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


Definition = namedtuple('Definition', 'type value')


class ResourceModule:

    def __init__(self, mosaic, resource_type_reg, resource_module_registry, name, path):
        self._mosaic = mosaic
        self._resource_type_reg = resource_type_reg
        self._resource_module_registry = resource_module_registry
        self._name = name
        self._path = path
        self._import_list = None

    def __contains__(self, var_name):
        return var_name in self._definitions

    def __getitem__(self, var_name):
        try:
            definition = self._definitions[var_name]
        except KeyError:
            raise RuntimeError(f"Resource module {self._name!r}: Unknown resource: {var_name!r}")
        piece = definition.type.resolve(definition.value, self._resolve_name)
        log.info("%s: Loaded resource %r: %s", self._name, var_name, piece)
        return piece

    def __iter__(self):
        return iter(self._definitions)

    def _resolve_name(self, name):
        if name in self._import_list:
            module_name, var_name = name.rsplit('.', 1)
            module = self._resource_module_registry[module_name]
            piece = module[var_name]
        else:
            piece = self[name]
        return self._mosaic.put(piece)

    @cached_property
    def _definitions(self):
        definitions, import_list = self._load()
        self._import_list = import_list
        return definitions

    def _load(self):
        log.info("Loading resource module %s: %s", self._name, self._path)
        contents = yaml.safe_load(self._path.read_text())
        import_list = contents.get('import', [])
        for name in import_list:
            module_name, var_name = name.rsplit('.', 1)
            try:
                module = self._resource_module_registry[module_name]
            except KeyError:
                raise RuntimeError(f"{self._name}: Importing {var_name} from unknown module: {module_name}")
            if var_name not in module:
                raise RuntimeError(f"{self._name}: Module {module_name} does not have {var_name!r}")
        definitions = {
            name: self._read_definition(name, contents)
            for name, contents in contents.get('definitions', {}).items()
            }
        return (definitions, import_list)

    def _read_definition(self, name, data):
        log.debug("%s: Load definition %r: %s", self._name, name, data)
        type_name = data['type']
        try:
            type = self._resource_type_reg[type_name]
        except KeyError:
            raise RuntimeError(f"Unsupported resource type: {type_name!r}")
        value = type.parse(data)
        return Definition(type, value)


def load_resource_modules(mosaic, resource_type_reg, dir_list):
    ext = '.resources.yaml'
    registry = {}
    for root_dir in dir_list:
        for path in root_dir.rglob(f'*{ext}'):
            if 'test' in path.relative_to(root_dir).parts:
                continue  # Skip test subdirectories.
            rpath = str(path.relative_to(root_dir))
            name = rpath[:-len(ext)].replace('/', '.')
            log.info("Resource module: %r", name)
            registry[name] = ResourceModule(mosaic, resource_type_reg, registry, name, path)
    return registry


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_module_registry = load_resource_modules(
            services.mosaic, services.resource_type_reg, services.module_dir_list)
