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
            path=None,
            allow_missing=False,
            ):
        self._mosaic = mosaic
        self._resource_type_producer = resource_type_producer
        self._resource_module_registry = resource_module_registry
        self._fixture_resource_module_registry = fixture_resource_module_registry
        self._python_object_creg = python_object_creg
        self._name = name
        self._path = path
        self._loaded_import_set = None
        self._loaded_definitions = None
        self._allow_missing = allow_missing

    def __contains__(self, var_name):
        return var_name in self._definitions

    def __getitem__(self, var_name):
        try:
            definition = self._definitions[var_name]
        except KeyError:
            raise RuntimeError(f"Resource module {self._name!r}: Unknown resource: {var_name!r}")
        piece = definition.type.resolve(definition.value, self._resolve_name, self._path.parent)
        log.info("%s: Loaded resource %r: %s", self._name, var_name, piece)
        return piece

    def __iter__(self):
        return iter(self._definitions)

    @property
    def name(self):
        return self._name

    def add_import(self, import_name):
        log.info("%s: Add import: %r", self._name, import_name)
        self._import_set.add(import_name)

    def set_definition(self, var_name, resource_type, definition_value):
        log.info("%s: Set definition %r, %s: %r", self._name, var_name, resource_type, definition_value)
        self._definitions[var_name] = Definition(resource_type, definition_value)

    def save(self):
        if self._path is None:
            raise RuntimeError(f"Attempt to save ethemeral resource module: {self._name}")
        self.save_as(self._path)

    def save_as(self, path):
        path.write_text(yaml.dump(self.as_dict, sort_keys=False))

    @property
    def as_dict(self):
        import_set = self._import_set
        definition_dict = {}
        for name, d in sorted(self._definitions.items()):
            t = d.type.definition_t
            type_name = f'legacy_type.{t.module_name}.{t.name}'
            definition_dict[name] = {
                '_type': type_name,
                **d.type.to_dict(d.value),
                }
            import_set.add(type_name)
        return {
            'import': sorted(import_set),
            'definitions': definition_dict,
            }

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
    def _definitions(self):
        self._ensure_loaded()
        return self._loaded_definitions

    @property
    def _import_set(self):
        self._ensure_loaded()
        return self._loaded_import_set

    def _ensure_loaded(self):
        if self._loaded_definitions is None:
            self._load()

    def _load(self):
        if self._path is None:
            self._loaded_import_set = set()
            self._loaded_definitions = {}
            return
        log.info("Loading resource module %s: %s", self._name, self._path)
        try:
            contents = yaml.safe_load(self._path.read_text())
        except FileNotFoundError:
            if not self._allow_missing:
                raise
            self._loaded_import_set = set()
            self._loaded_definitions = {}
            return
        self._loaded_import_set = set(contents.get('import', []))
        self._loaded_definitions = {}
        for name in self._loaded_import_set:
            module_name, var_name = name.rsplit('.', 1)
            try:
                module = self._resource_module_registry[module_name]
            except KeyError:
                raise RuntimeError(f"{self._name}: Importing {var_name} from unknown module: {module_name}")
            if var_name not in module:
                raise RuntimeError(f"{self._name}: Module {module_name} does not have {var_name!r}")
        for name, contents in contents.get('definitions', {}).items():
            self._loaded_definitions[name] = self._read_definition(name, contents)

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
