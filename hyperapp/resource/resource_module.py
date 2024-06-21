import logging
import yaml
from collections import namedtuple
from functools import cached_property

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.resource.resource_registry import UnknownResourceName
from hyperapp.common.association_registry import Association

log = logging.getLogger(__name__)


AUTO_GEN_LINE = '# Automatically generated file. Do not edit.'

Definition = namedtuple('Definition', 'type value')
_Association = namedtuple('_Association', 'bases key value')


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
            imports=None,
            definitions=None,
            associations=None,
            ):
        self._mosaic = mosaic
        self._resource_type_producer = resource_type_producer
        self._resource_registry = resource_registry
        self._pyobj_creg = pyobj_creg
        self._name = name
        self._path = path
        self._resource_dir = path.parent if path else None
        self._loaded_imports = imports
        self._loaded_definitions = definitions
        self._loaded_associations = associations
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

    @cached_property
    def is_auto_generated(self):
        lines = self._path.read_text().splitlines()
        return len(lines) >= 1 and lines[0] == AUTO_GEN_LINE

    @cached_property
    def source_ref_str(self):
        return self._read_hash_line(0)

    @cached_property
    def tests_ref_str(self):
        return self._read_hash_line(1)

    @cached_property
    def generator_ref_str(self):
        return self._read_hash_line(2)

    def _read_hash_line(self, idx):
        path = self._hash_file_path(self._path)
        if not path.exists():
            return None
        lines = path.read_text().splitlines()
        return lines[idx]

    @property
    def used_imports(self):
        module_set = set()
        if self._loaded_definitions is None:
            # Do not try to resolve if not loaded.
            module_contents = self._module_contents
            import_set = set(module_contents.get('import', []))
        else:
            import_set = self._import_set
        for name in import_set:
            module_name, var_name = name.split(':')
            module_set.add((module_name, var_name))
        return module_set

    def code_module_imports(self, code_name):
        assert self._loaded_definitions is None  # Not expecting it to be already loaded.
        module_contents = self._module_contents
        return module_contents['definitions'][f'{code_name}.module']['value']['import_list']

    @property
    def provided_services(self):
        services = set()
        if self._loaded_definitions is None:
            # Do not try to resolve if not loaded.
            module_contents = self._module_contents
            definitions = set(module_contents.get('definitions', []))
        else:
            definitions = self._definition_dict
        for name in definitions:
            l = name.split('.')
            if len(l) == 2 and l[1] == 'service':
                services.add(l[0])
        return services

    def add_association_list(self, ass_list):
        for ass in ass_list:
            self.add_association(ass)

    def add_association(self, ass):
        log.info("%s: Add association: %r", self._name, ass)
        key = ass.key
        if type(key) not in {tuple, list}:
            key = [key]
        self._association_list.append(_Association(
            bases=[self._reverse_resolve(b) for b in ass.bases],
            key=[self._reverse_resolve(k) for k in key],
            value=self._reverse_resolve(ass.value),
            ))

    def _resource_to_definition(self, resource):
        resource_t = deduce_value_type(resource)
        t = self._resource_type_producer(resource_t)
        definition = t.reverse_resolve(resource, self._resolve_ref, self._resource_dir)
        return (t, definition)

    @property
    def name(self):
        return self._name

    def with_module(self, module):
        return ResourceModule(
            mosaic=self._mosaic,
            resource_type_producer=self._resource_type_producer,
            pyobj_creg=self._pyobj_creg,
            resource_registry=self._resource_registry,
            name=f'{self._name}-with-{module.name}',
            path=self._path.with_name('dummy'),
            load_from_file=True,
            imports=self._import_set | module._import_set,
            definitions={**self._definition_dict, **module._definition_dict},
            associations=self._association_list + module._association_list,
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

    def add_association_def(self, resource_type, definition):
        assert 0, repr(definition)
        log.info("%s: Add association definition %s: %r", self._name, resource_type, definition)
        self._association_list.add(Definition(resource_type, definition))
        self._import_set.add(self._resource_type_name(resource_type))

    def save_as(self, path, source_ref_str, tests_ref_str, generator_ref_str):
        yaml_text = yaml.dump(self.as_dict, sort_keys=False)
        lines = [
            AUTO_GEN_LINE,
            '',
            yaml_text,
            ]
        path.write_text('\n'.join(lines))
        hash_lines = [source_ref_str, tests_ref_str, generator_ref_str]
        self._hash_file_path(path).write_text('\n'.join(hash_lines))
        self._path = path
        self._resource_dir = path.parent

    def _hash_file_path(self, path):
        return path.with_suffix('.hash')

    @property
    def as_dict(self):
        return {
            'import': sorted(self._import_set),
            'associations': [
                self._association_as_dict(ass)
                for ass in sorted(self._association_list)
                ],
            'definitions': {
                name: self._definition_as_dict(d)
                for name, d in sorted(self._definition_dict.items())
                },
            }

    def _definition_as_dict(self, definition):
        return {
            'type': self._resource_type_name(definition.type),
            'value': definition.type.to_dict(definition.value),
            }

    def _association_as_dict(self, ass):
        key = ass.key
        if len(key) == 1:
            [key] = key
        d = {}
        if ass.bases:
            d['bases'] = ass.bases
        return {
            **d,
            'key': key,
            'value': ass.value,
            }

    def _resource_type_name(self, resource_type):
        t = resource_type.resource_t
        assert t.module_name and t.name, t  # Only named types are supported.
        return f'legacy_type.{t.module_name}:{t.name}'

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

    @property
    def _association_list(self):
        self._ensure_loaded()
        return self._loaded_associations

    @property
    def associations(self):
        ass_list = []
        for ass in self._association_list:
            bases, key, value = self._resolve_association(ass)
            if len(key) == 1:
                [key] = key
            else:
                key = tuple(key)
            ass_list.append(Association(
                bases=bases,
                key=key,
                value=value,
                ))
        return ass_list

    def _ensure_loaded(self):
        if self._loaded_definitions is None:
            self._load()

    def _load(self):
        self._loaded_imports = set()
        self._loaded_definitions = {}
        self._loaded_associations = []
        if self._path is None or not self._load_from_file:
            return
        log.info("Loading resource module %s: %s", self._name, self._path)
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
        for contents in module_contents.get('associations', []):
            self._loaded_associations.append(self._read_association(contents))

    @cached_property
    def _module_contents(self):
        return yaml.safe_load(self._path.read_text())

    def _read_definition(self, name, data):
        log.debug("%s: Load definition %r: %s", self._name, name, data)
        try:
            resource_t_name = data['type']
            resource_value = data['value']
        except KeyError as x:
            raise RuntimeError(f"{self._name}: definition {name!r} has no {e.args[0]!r} attribute")
        resource_t_res = self._resolve_name(resource_t_name)
        resource_t = self._pyobj_creg.animate(resource_t_res)
        t = self._resource_type_producer(resource_t)
        try:
            value = t.from_dict(resource_value)
        except Exception as x:
            raise RuntimeError(f"Error loading definition {self._name}/{name}: {x}")
        return Definition(t, value)

    def _read_association(self, data):
        log.debug("%s: Load association: %s", self._name, data)
        bases = data.get('bases', [])
        try:
            key = data['key']
            value = data['value']
        except KeyError as x:
            raise RuntimeError(f"{self._name}: Invalid association: Missing key: {x}. Value: {data}")
        if isinstance(key, str):
            key = [key]
        elif not isinstance(key, list):
            raise RuntimeError(f"{self._name}: Invalid association value: Expected string or list, but got: {key}")
        ass = _Association(bases, key, value)
        _ = self._resolve_association(ass)
        return ass

    def _resolve_association(self, ass):
        return (
            [self._resolve_name(b) for b in ass.bases],
            [self._resolve_name(n) for n in ass.key],
            self._resolve_name(ass.value),
            )


def load_resource_modules(resource_module_factory, resource_dir, resource_registry):
    for rp in resource_dir.enum():
        log.debug("Resource module: %r", rp.name)
        resource_registry.set_module(rp.name, resource_module_factory(resource_registry, rp.name, rp.path))


def load_resource_modules_list(resource_module_factory, resource_dir_list, resource_registry):
    for resource_dir in resource_dir_list:
        load_resource_modules(resource_module_factory, resource_dir, resource_registry)
