import logging
import yaml
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

from .resource_registry import UnknownResourceName

log = logging.getLogger(__name__)


Definition = namedtuple('Definition', 'type value')


class ResourceModule:

    def __init__(
            self,
            mosaic,
            resource_type_producer,
            python_object_creg,
            resource_registry,
            name,
            path=None,
            load_from_file=True,
            imports=None,
            definitions=None,
            associations=None,
            ):
        self._mosaic = mosaic
        self._resource_type_producer = resource_type_producer
        self._resource_registry = resource_registry
        self._python_object_creg = python_object_creg
        self._name = name
        self._path = path
        self._resource_dir = path.parent if path else None
        self._loaded_imports = imports
        self._loaded_definitions = definitions
        self._loaded_associations = associations
        self._load_from_file = load_from_file and path is not None

    def __contains__(self, var_name):
        return var_name in self._definition_dict

    def __getitem__(self, var_name):
        try:
            definition = self._definition_dict[var_name]
        except KeyError:
            raise KeyError(f"Resource module {self._name!r}: Unknown resource: {var_name!r}")
        piece = definition.type.resolve(definition.value, self._resolve_name, self._resource_dir)
        log.info("%s: Loaded resource %r: %s", self._name, var_name, piece)
        return piece

    def __setitem__(self, name, resource):
        resource_t = deduce_value_type(resource)
        t = self._resource_type_producer(resource_t)
        definition = t.reverse_resolve(resource, self._resolve_ref, self._resource_dir)
        self.set_definition(name, t, definition)

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
            resource_registry=self._resource_registry,
            name=f'{self._name}-with-{module.name}',
            path=self._path.with_name('dummy'),
            load_from_file=True,
            imports=self._import_set | module._import_set,
            definitions={**self._definition_dict, **module._definition_dict},
            associations=self._association_set | module._association_set,
            )

    def add_import(self, import_name):
        log.info("%s: Add import: %r", self._name, import_name)
        self._import_set.add(import_name)

    def remove_import(self, import_name):
        log.info("%s: Remove import: %r", self._name, import_name)
        self._import_set.remove(import_name)

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
        yaml_text = yaml.dump(self.as_dict, sort_keys=False)
        path.write_text(f'# Automatically generated file. Do not edit.\n\n' + yaml_text)

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
        t = resource_type.resource_t
        return f'legacy_type.{t.module_name}:{t.name}'

    def _resolve_name(self, name):
        if name in self._import_set:
            module_name, var_name = name.split(':')
        else:
            assert ':' not in name
            module_name = self._name
            var_name = name
        piece = self._resource_registry[module_name, var_name]
        return self._mosaic.put(piece)

    def _resolve_ref(self, resource_ref):
        resource = self._mosaic.resolve_ref(resource_ref).value
        module_name, var_name = self._resource_registry.reverse_resolve(resource)
        if module_name == self._name:
            return var_name
        else:
            full_name = f'{module_name}:{var_name}'
            self._import_set.add(full_name)
            return full_name

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
        if self._path is None or not self._load_from_file:
            return
        log.info("Loading resource module %s: %s", self._name, self._path)
        module_contents = yaml.safe_load(self._path.read_text())
        self._loaded_imports = set(module_contents.get('import', []))
        for name in self._loaded_imports:
            try:
                module_name, var_name = name.split(':')
                self._resource_registry.check_has_name((module_name, var_name))
            except UnknownResourceName as x:
                raise RuntimeError(f"{self._name}: Importing {name!r}: {x}")
        for name, contents in module_contents.get('definitions', {}).items():
            self._loaded_definitions[name] = self._read_definition(name, contents)
        for contents in module_contents.get('associations', []):
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
        try:
            value = t.from_dict(data)
        except Exception as x:
            raise RuntimeError(f"Error loading definition {self._name}/{name}: {x}")
        return Definition(t, value)


def load_resource_modules(resource_module_factory, resource_dir, resource_registry):
    for rp in resource_dir.enum():
        log.info("Resource module: %r", rp.name)
        resource_registry.set_module(rp.name, resource_module_factory(resource_registry, rp.name, rp.path))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_module_factory = resource_module_factory = partial(
            ResourceModule,
            services.mosaic,
            services.resource_type_producer,
            services.python_object_creg,
        )
        services.resource_loader = resource_loader = partial(
            load_resource_modules,
            resource_module_factory,
            )
        for resource_dir in services.resource_dir_list:
            resource_loader(resource_dir, services.resource_registry)
