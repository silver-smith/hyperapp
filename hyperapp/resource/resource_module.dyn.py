import logging
import yaml
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


Definition = namedtuple('Definition', 'type value')


class ResourceModule:

    def __init__(
            self,
            mosaic,
            resource_type_producer,
            python_object_creg,
            resource_module_registry,
            fixture_resource_module_registry,
            name,
            path,
            allow_missing=False,
            imports=None,
            definitions=None,
            associations=None,
            ):
        self._mosaic = mosaic
        self._resource_type_producer = resource_type_producer
        self._resource_module_registry = resource_module_registry
        self._fixture_resource_module_registry = fixture_resource_module_registry
        self._python_object_creg = python_object_creg
        self._name = name
        self._path = path
        self._loaded_imports = imports
        self._loaded_definitions = definitions
        self._loaded_associations = associations
        self._allow_missing = allow_missing

    def __contains__(self, var_name):
        return var_name in self._definition_dict

    def __getitem__(self, var_name):
        try:
            definition = self._definition_dict[var_name]
        except KeyError:
            raise RuntimeError(f"Resource module {self._name!r}: Unknown resource: {var_name!r}")
        piece = definition.type.resolve(definition.value, self._resolve_name, self._path.parent)
        log.info("%s: Loaded resource %r: %s", self._name, var_name, piece)
        return piece

    def __iter__(self):
        return iter(self._definition_dict)

    @property
    def name(self):
        return self._name

    def with_module(self, module):
        return ResourceModule(
            mosaic=self._mosaic,
            resource_type_producer=self._resource_type_producer,
            python_object_creg=self._python_object_creg,
            resource_module_registry=self._resource_module_registry,
            fixture_resource_module_registry=self._fixture_resource_module_registry,
            name=f'{self._name}-with-{module.name}',
            path=self._path.with_name('dummy'),
            allow_missing=True,
            imports=self._import_set | module._import_set,
            definitions={**self._definition_dict, **module._definition_dict},
            associations=self._association_set | module._association_set,
            )

    def add_import(self, import_name):
        log.info("%s: Add import: %r", self._name, import_name)
        self._import_set.add(import_name)

    def set_definition(self, var_name, resource_type, definition_value):
        log.info("%s: Set definition %r, %s: %r", self._name, var_name, resource_type, definition_value)
        self._definition_dict[var_name] = Definition(resource_type, definition_value)
        self._import_set.add(self._resource_type_name(resource_type))

    def add_association(self, resource_type, definition_value):
        log.info("%s: Add association %s: %r", self._name, resource_type, definition_value)
        self._association_set.add(Definition(resource_type, definition_value))
        self._import_set.add(self._resource_type_name(resource_type))

    def save(self):
        if self._path is None:
            raise RuntimeError(f"Attempt to save ethemeral resource module: {self._name}")
        self.save_as(self._path)

    def save_as(self, path):
        path.write_text(yaml.dump(self.as_dict, sort_keys=False))

    @property
    def as_dict(self):
        return {
            'import': sorted(self._import_set),
            'associations': [
                self._definition_as_dict(d)
                for d in sorted(self._association_set)
                ],
            'definitions': {
                name: self._definition_as_dict(d)
                for name, d in sorted(self._definition_dict.items())
                },
            }

    def _definition_as_dict(self, definition):
        return {
            '_type': self._resource_type_name(definition.type),
            **definition.type.to_dict(definition.value),
            }

    def _resource_type_name(self, resource_type):
        t = resource_type.definition_t
        return f'legacy_type.{t.module_name}.{t.name}'

    def _resolve_name(self, name):
        if name in self._import_set:
            module_name, var_name = name.rsplit('.', 1)
            if module_name.endswith('.fixtures'):
                module = self._fixture_resource_module_registry[module_name]
            else:
                module = self._resource_module_registry[module_name]
            piece = module[var_name]
        else:
            piece = self[name]
        return self._mosaic.put(piece)

    @property
    def _import_set(self):
        self._ensure_loaded()
        return self._loaded_imports

    @property
    def _definition_dict(self):
        self._ensure_loaded()
        return self._loaded_definitions

    @property
    def _association_set(self):
        self._ensure_loaded()
        return self._loaded_associations

    @property
    def associations(self):
        return {
            d.type.resolve(d.value, self._resolve_name, self._path.parent)
            for d in self._association_set
            }

    def _ensure_loaded(self):
        if self._loaded_definitions is None:
            self._load()

    def _load(self):
        self._loaded_imports = set()
        self._loaded_definitions = {}
        self._loaded_associations = set()
        if self._path is None:
            return
        log.info("Loading resource module %s: %s", self._name, self._path)
        try:
            contents = yaml.safe_load(self._path.read_text())
        except FileNotFoundError:
            if not self._allow_missing:
                raise
            return
        self._loaded_imports = set(contents.get('import', []))
        for name in self._loaded_imports:
            module_name, var_name = name.rsplit('.', 1)
            try:
                module = self._resource_module_registry[module_name]
            except KeyError:
                raise RuntimeError(f"{self._name}: Importing {var_name} from unknown module: {module_name}")
            if var_name not in module:
                raise RuntimeError(f"{self._name}: Module {module_name} does not have {var_name!r}")
        for name, contents in contents.get('definitions', {}).items():
            self._loaded_definitions[name] = self._read_definition(name, contents)
        for contents in contents.get('associations', {}).items():
            name = contents.get('_type')  # Just for logging and error strings.
            self._loaded_associations.add(self._read_definition(name, contents))

    def _read_definition(self, name, data):
        log.debug("%s: Load definition %r: %s", self._name, name, data)
        try:
            resource_t_name = data['_type']
        except KeyError:
            raise RuntimeError(f"{self._name}: definition {name!r} has no '_type' attribute")
        resource_t_res = self._resolve_name(resource_t_name)
        resource_t = self._python_object_creg.invite(resource_t_res)
        t = self._resource_type_producer(resource_t)
        value = t.from_dict(data)
        return Definition(t, value)


def load_resource_modules(mosaic, resource_type_producer, python_object_creg, dir_list):
    ext = '.resources.yaml'
    fixture_ext = '.fixtures.resources.yaml'
    registry = {}
    fixture_registry = {}
    for root_dir in dir_list:
        for path in root_dir.rglob(f'*{ext}'):
            if 'test' in path.relative_to(root_dir).parts:
                continue  # Skip test subdirectories.
            rpath = str(path.relative_to(root_dir))
            name = rpath[:-len(ext)].replace('/', '.')
            if str(path).endswith(fixture_ext):
                log.info("Fixture resource module: %r", name)
                fixture_registry[name] = ResourceModule(
                    mosaic, resource_type_producer, python_object_creg, registry, fixture_registry, name, path)
            else:
                log.info("Resource module: %r", name)
                registry[name] = ResourceModule(
                    mosaic, resource_type_producer, python_object_creg, registry, fixture_registry, name, path)
    return (registry, fixture_registry)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_module_registry, services.fixture_resource_module_registry = load_resource_modules(
            services.mosaic,
            services.resource_type_producer,
            services.python_object_creg,
            services.module_dir_list,
        )
        services.resource_module_factory = partial(
            ResourceModule,
            services.mosaic,
            services.resource_type_producer,
            services.python_object_creg,
            services.resource_module_registry,
            services.fixture_resource_module_registry,
        )
