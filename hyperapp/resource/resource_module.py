import logging
import yaml
from collections import namedtuple
from functools import cached_property

from yaml.scanner import ScannerError

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.resource.resource_registry import UnknownResourceName

log = logging.getLogger(__name__)


AUTO_GEN_LINE = '# Automatically generated file. Do not edit.'

Definition = namedtuple('Definition', 'type value')


class ResourceModule:

    def __init__(
            self,
            mosaic,
            resource_type_producer,
            pyobj_creg,
            resource_registry,
            name,
            path=None,
            load_from_file=True,
            text=None,
            resource_dir=None,
            imports=None,
            definitions=None,
            ):
        self._mosaic = mosaic
        self._resource_type_producer = resource_type_producer
        self._resource_registry = resource_registry
        self._pyobj_creg = pyobj_creg
        self._name = name
        self._path = path
        self._text = text
        self._resource_dir = resource_dir or (path.parent if path else None)
        self._loaded_imports = imports
        self._loaded_definitions = definitions
        self._load_from_file = load_from_file and path is not None

    def __repr__(self):
        return f"<ResourceModule {self._name}>"

    def __iter__(self):
        return iter(self._definition_dict)

    def __contains__(self, var_name):
        return var_name in self._definition_dict

    def __getitem__(self, var_name):
        try:
            definition = self._definition_dict[var_name]
        except KeyError:
            raise KeyError(f"Resource module {self._name!r}: Unknown resource: {var_name!r}")
        piece = definition.type.resolve(definition.value, self._resolve_name_to_ref, self._resource_dir)
        self._resource_registry.add_to_cache((self._name, var_name), piece)
        log.debug("%s: Loaded resource %r: %s", self._name, var_name, piece)
        return piece

    def __setitem__(self, name, resource):
        log.info("%s: Set resource %r: %r", self._name, name, resource)
        t, definition = self._resource_to_definition(resource)
        self.set_definition(name, t, definition)
        self._resource_registry.add_to_cache((self._name, name), resource)

    def __delitem__(self, var_name):
        del self._definition_dict[var_name]
        self._resource_registry.remove_from_cache((self._name, var_name))

    def clear(self):
        for var_name in self._definition_dict:
            self._resource_registry.remove_from_cache((self._name, var_name))
        self._definition_dict.clear()
        self._loaded_imports = set()
        self._loaded_definitions = {}

    def _resource_to_definition(self, resource):
        resource_t = deduce_value_type(resource)
        t = self._resource_type_producer(resource_t)
        definition = t.reverse_resolve(resource, self._resolve_ref, self._resource_dir)
        return (t, definition)

    @property
    def name(self):
        return self._name

    def _add_resource_type(self, resource_type):
        piece = self._pyobj_creg.actor_to_piece(resource_type.resource_t)
        if self._resource_registry.has_piece(piece):
            _ = self._reverse_resolve(piece)  # Adds to import_set.
            return
        self[piece.name] = piece
        return piece.name

    def set_definition(self, var_name, resource_type, definition_value):
        log.info("%s: Set definition %r, %s: %r", self._name, var_name, resource_type, definition_value)
        custom_type_name = self._add_resource_type(resource_type)
        if custom_type_name and var_name == custom_type_name:
            raise RuntimeError(f"Custom type name matches variable name: {var_name!r}")
        self._definition_dict[var_name] = Definition(resource_type, definition_value)

    @property
    def as_dict(self):
        d = {}
        d['import'] = sorted(self._import_set)
        d['definitions'] = {
            name: self._definition_as_dict(d)
            for name, d in sorted(self._definition_dict.items())
            }
        return d

    @property
    def as_text(self):
        yaml_text = yaml.dump(self.as_dict, sort_keys=False)
        lines = [
            AUTO_GEN_LINE,
            '',
            yaml_text,
            ]
        return '\n'.join(lines)

    def _resolve_resource_type(self, resource_type):
        piece = self._pyobj_creg.actor_to_piece(resource_type.resource_t)
        return self._reverse_resolve(piece)

    def _definition_as_dict(self, definition):
        return {
            'type': self._resolve_resource_type(definition.type),
            'value': definition.type.to_dict(definition.value),
            }

    def _resolve_name(self, name):
        if ':' in name:
            if name not in self._import_set:
                raise RuntimeError(f"{self._name}: Full path is not in imports: {name!r}")
            module_name, var_name = name.split(':')
        else:
            module_name = self._name
            var_name = name
        return self._resource_registry[module_name, var_name]

    def _resolve_name_to_ref(self, name):
        return self._mosaic.put(self._resolve_name(name))

    def _resolve_ref(self, resource_ref):
        resource = self._mosaic.resolve_ref(resource_ref).value
        return self._reverse_resolve(resource)

    def _reverse_resolve(self, resource):
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

    def _ensure_loaded(self):
        if self._loaded_definitions is None:
            self._load()

    def _load(self):
        self._loaded_imports = set()
        self._loaded_definitions = {}
        if self._text:
            log.info("Loading resource module %s (%d bytes)", self._name, len(self._text))
        elif self._path and self._load_from_file:
            log.debug("Loading resource module %s: %s", self._name, self._path)
        else:
            return
        module_contents = self._module_contents
        self._loaded_imports = set(module_contents.get('import', []))
        for name in self._loaded_imports:
            try:
                module_name, var_name = name.split(':')
                self._resource_registry.check_has_name((module_name, var_name))
            except (UnknownResourceName, ValueError) as x:
                raise RuntimeError(f"{self._name}: Importing {name!r}: {x}")
        for name, contents in module_contents.get('definitions', {}).items():
            self._loaded_definitions[name] = self._read_definition(name, contents)

    @cached_property
    def _module_contents(self):
        if self._text:
            text = self._text
        else:
            text = self._path.read_text()
        try:
            return yaml.safe_load(text)
        except ScannerError as x:
            if self._text:
                raise
            raise RuntimeError(f"In {self._path}: {x}") from x

    def _read_definition(self, name, data):
        log.debug("%s: Load definition %r: %s", self._name, name, data)
        try:
            resource_t_name = data['type']
            resource_value = data['value']
        except KeyError as x:
            raise RuntimeError(f"{self._name}: definition {name!r} has no {x.args[0]!r} attribute")
        resource_t_res = self._resolve_name(resource_t_name)
        resource_t = self._pyobj_creg.animate(resource_t_res)
        t = self._resource_type_producer(resource_t)
        try:
            value = t.from_dict(resource_value)
        except Exception as x:
            raise RuntimeError(f"Error loading definition {self._name}/{name}: {x}")
        return Definition(t, value)


def load_resource_modules(resource_module_factory, resource_dir, resource_registry):
    for rp in resource_dir.enum():
        log.debug("Resource module: %r", rp.name)
        resource_registry.set_module(rp.name, resource_module_factory(resource_registry, rp.name, rp.path))


def load_resource_modules_list(resource_module_factory, resource_dir_list, resource_registry):
    for resource_dir in resource_dir_list:
        load_resource_modules(resource_module_factory, resource_dir, resource_registry)
