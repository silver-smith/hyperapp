import logging
import yaml
from collections import namedtuple
from functools import cached_property, partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


Definition = namedtuple('Definition', 'type value')


class ResourceModule:

    def __init__(self, mosaic, resource_type_reg, resource_module_registry, name, path, allow_missing=False):
        self._mosaic = mosaic
        self._resource_type_reg = resource_type_reg
        self._resource_module_registry = resource_module_registry
        self._name = name
        self._path = path
        self._import_set = None
        self._should_load = True
        self._allow_missing = allow_missing

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

    def add_import(self, import_name):
        log.info("%s: Add import: %r", self._name, import_name)
        self._definitions  # Force loading.
        self._import_set.add(import_name)

    def set_definition(self, var_name, resource_type, definition_value):
        log.info("%s: Set definition %r, %s: %r", self._name, var_name, resource_type, definition_value)
        self._definitions[var_name] = Definition(resource_type, definition_value)

    def save(self):
        self._path.write_text(yaml.dump(self.as_dict, sort_keys=False))

    @property
    def as_dict(self):
        definitions = self._definitions  # Load before imports_set is used.
        return {
            'import': sorted(self._import_set),
            'definitions': {
                name: {
                    'type': d.type.name,
                    **d.type.to_dict(d.value),
                    }
                for name, d in sorted(definitions.items())
                },
            }

    def _resolve_name(self, name):
        if name in self._import_set:
            module_name, var_name = name.rsplit('.', 1)
            module = self._resource_module_registry[module_name]
            piece = module[var_name]
        else:
            piece = self[name]
        return self._mosaic.put(piece)

    @cached_property
    def _definitions(self):
        definitions, import_set = self._load()
        self._import_set = import_set
        return definitions

    def _load(self):
        log.info("Loading resource module %s: %s", self._name, self._path)
        try:
            contents = yaml.safe_load(self._path.read_text())
        except FileNotFoundError:
            if not self._allow_missing:
                raise
            return ({}, set())
        import_set = set(contents.get('import', []))
        for name in import_set:
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
        return (definitions, import_set)

    def _read_definition(self, name, data):
        log.debug("%s: Load definition %r: %s", self._name, name, data)
        type_name = data['type']
        try:
            type = self._resource_type_reg[type_name]
        except KeyError:
            raise RuntimeError(f"Unsupported resource type: {type_name!r}")
        value = type.from_dict(data)
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
        services.resource_module_factory = partial(
            ResourceModule, services.mosaic, services.resource_type_reg, services.resource_module_registry)
