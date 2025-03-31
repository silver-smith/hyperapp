import logging
import yaml
from collections import namedtuple
from dataclasses import dataclass
from functools import cached_property

from yaml.scanner import ScannerError

from hyperapp.boot.htypes import record_mt, list_mt
from hyperapp.boot.htypes.deduce_value_type import deduce_value_type
from hyperapp.boot.resource.resource_registry import UnknownResourceName

log = logging.getLogger(__name__)


AUTO_GEN_LINE = '# Automatically generated file. Do not edit.'


@dataclass
class _Data:
    type: str
    value: dict

    @property
    def as_dict(self):
        return {
            'type': self.type,
            'value': self.value,
            }


class ResourceModule:

    _Definition = namedtuple('_Definition', 'type value')

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
            data_dicts=None,
            definitions=None,
            items=None,
            ):
        self._mosaic = mosaic
        self._resource_type_producer = resource_type_producer
        self._resource_registry = resource_registry
        self._pyobj_creg = pyobj_creg
        self._name = name
        self._path = path
        self._text = text
        self._resource_dir = resource_dir or (path.parent if path else None)
        self._import_set = imports
        self._definitions = definitions  # name -> _Definition
        self._data = data_dicts  # name -> _Data
        self._items = items  # name -> piece
        self._load_from_file = load_from_file and path is not None

    def __repr__(self):
        return f"<ResourceModule {self._name}>"

    @property
    def name(self):
        return self._name

    def __iter__(self):
        self._ensure_loaded()
        return iter(self._all_names)

    def __contains__(self, var_name):
        self._ensure_loaded()
        return var_name in self._definitions or var_name in self._data

    def __getitem__(self, name):
        self._ensure_loaded()
        return self._get(name)

    def __setitem__(self, name, piece):
        self._ensure_loaded()
        log.info("%s: Set resource %r: %r", self._name, name, piece)
        self._set(name, piece)

    def __delitem__(self, name):
        self._ensure_loaded()
        try:
            del self._items[name]
        except KeyError:
            pass
        try:
            del self._definitions[name]
        except KeyError:
            pass
        else:
            del self._data[name]
        self._resource_registry.remove_from_cache((self._name, name))

    def clear(self):
        self._ensure_loaded()
        for name in self._all_names:
            self._resource_registry.remove_from_cache((self._name, name))
        self._definitions.clear()
        self._import_set = set()
        self._definitions = {}
        self._data = {}
        self._items = {}

    @property
    def _is_loaded(self):
        return self._data is not None

    @property
    def _all_names(self):
        return {*self._data, *self._definitions}

    def _resolve_data(self, name, data):
        resource_t_res = self._resolve_name(data.type)
        resource_t = self._pyobj_creg.animate(resource_t_res)
        t = self._resource_type_producer(resource_t)
        try:
            value = t.from_dict(data.value)
        except Exception as x:
            raise RuntimeError(f"Error resolving definition {self._name}/{name}: {x}")
        return self._Definition(t, value)

    def _get_data(self, name):
        try:
            return self._data[name]
        except KeyError:
            pass
        defn = self._definitions[name]
        data = _Data(
            type=self._resolve_resource_type(defn.type),
            value=defn.type.to_dict(defn.value),
            )
        self._data[name] = data
        return data

    def _get_definition(self, name):
        try:
            return self._definitions[name]
        except KeyError:
            pass
        try:
            data = self._data[name]
        except KeyError:
            raise KeyError(f"Resource module {self._name!r}: Unknown resource: {name!r}")
        defn = self._resolve_data(name, data)
        self._definitions[name] = defn
        return defn

    def _get(self, name):
        try:
            return self._items[name]
        except KeyError:
            pass
        defn = self._get_definition(name)  # KeyError from here.
        try:
            piece = defn.type.resolve(defn.value, self._resolve_name_to_ref, self._resource_dir)
            self._items[name] = piece
            self._resource_registry.add_to_cache((self._name, name), piece)
            log.debug("%s: Loaded resource %r: %s", self._name, name, piece)
            return piece
        except KeyError as x:
            # KeyError risen from __getitem__ will be swallowed.
            raise RuntimeError(f"While resolving {self._name}:{name}: {x}") from x

    def _set(self, name, piece):
        definition = self._piece_to_definition(piece)
        self._set_definition(name, definition)
        self._items[name] = piece
        self._resource_registry.add_to_cache((self._name, name), piece)

    def _piece_to_definition(self, piece):
        piece_t = deduce_value_type(piece)
        type = self._resource_type_producer(piece_t)
        value = type.reverse_resolve(piece, self._resolve_ref, self._resource_dir)
        return self._Definition(type, value)

    def _set_definition(self, name, definition):
        log.info("%s: Set definition %r, %s: %r", self._name, name, definition.type, definition.value)
        custom_type_name = self._add_resource_type(definition.type)
        if custom_type_name and name == custom_type_name:
            raise RuntimeError(f"Custom type name matches variable name: {name!r}")
        self._definitions[name] = definition
        try:
            del self._data[name]
        except KeyError:
            pass
        try:
            del self._items[name]
        except KeyError:
            pass

    def _add_resource_type(self, resource_type):
        piece = self._pyobj_creg.actor_to_piece(resource_type.resource_t)
        if self._resource_registry.has_piece(piece):
            full_name = self._reverse_resolve(piece)  # Adds to import_set.
            if ':' in full_name:
                return (full_name
                        .removeprefix('legacy_type.')
                        .replace(':', '-')
                        )
            else:
                return full_name
        if isinstance(piece, record_mt):
            name = piece.name
        elif isinstance(piece, list_mt):
            element_t = resource_type.resource_t.element_t
            element_type = self._resource_type_producer(element_t)
            element_name = self._add_resource_type(element_type)
            name = f'{element_name}-list'
        self._set(name, piece)
        return name

    @property
    def as_dict(self):
        self._ensure_loaded()
        d = {}
        if self._import_set:
            d['import'] = sorted(self._import_set)
        d['definitions'] = {
            name: self._get_data(name).as_dict
            for name in sorted(self._all_names)
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

    def save(self):
        self._path.write_text(self.as_text)

    def _resolve_resource_type(self, resource_type):
        piece = self._pyobj_creg.actor_to_piece(resource_type.resource_t)
        return self._reverse_resolve(piece)

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

    def _ensure_loaded(self):
        if not self._is_loaded:
            self._load()

    def _load(self):
        self._import_set = set()
        self._definitions = {}
        self._data = {}
        self._items = {}
        if self._text:
            log.debug("Loading resource module %s (%d bytes)", self._name, len(self._text))
        elif self._path and self._load_from_file:
            log.debug("Loading resource module %s: %s", self._name, self._path)
        else:
            return
        module_contents = self._module_contents
        self._import_set = set(module_contents.get('import', []))
        for name in self._import_set:
            try:
                module_name, var_name = name.split(':')
                self._resource_registry.check_has_name((module_name, var_name))
            except (UnknownResourceName, ValueError) as x:
                raise RuntimeError(f"{self._name}: Importing {name!r}: {x}")
        for name, contents in module_contents.get('definitions', {}).items():
            self._data[name] = self._read_data(name, contents)

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

    def _read_data(self, name, data):
        log.debug("%s: Load %r: %s", self._name, name, data)
        try:
            type_name = data['type']
            value_dict = data['value']
        except KeyError as x:
            raise RuntimeError(f"{self._name}: definition {name!r} has no {x.args[0]!r} attribute")
        return _Data(type_name, value_dict)
