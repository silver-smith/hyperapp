import uuid

from .htypes import (
    ref_t,
    TypeNamespace,
    TypeNameResolver,
    make_meta_type_registry,
    tNamed,
    t_named,
    t_ref,
    builtin_ref_t,
    meta_ref_t,
    )
from .mapper import Mapper


class LocalTypeModule(object):

    def __init__(self):
        self._name2ref = {}  # name -> meta_ref_t

    def register(self, name, ref):
        assert isinstance(ref, ref_t), repr(ref)
        self._name2ref[name] = ref

    def resolve(self, name):
        return self._name2ref.get(name)


class LocalTypeModuleRegistry(object):

    def __init__(self):
        self._registry = {}

    def register(self, name, local_type_module):
        assert isinstance(local_type_module, LocalTypeModule), repr(local_type_module)
        self._registry[name] = local_type_module

    def resolve(self, name):
        return self._registry.get(name)


class TypeModuleToRefsMapper(Mapper):

    def __init__(self, buildin_types_registry, ref_registry, local_name_dict):
        self._buildin_types_registry = buildin_types_registry
        self._ref_registry = ref_registry
        self._local_name_dict = local_name_dict

    def map_hierarchy_obj(self, tclass, value):
        if tclass is tNamed:
            return self._map_named_t(value)
        return value

    def _map_named_t(self, rec):
        ref = self._local_name_dict.get(rec.name)
        if ref:
            return t_ref(ref)
        t = self._buildin_types_registry.resolve(['basic', rec.name])
        assert t, repr(rec.name)  # Unknown name, must be caught by type loader
        return t_ref(self._make_builtin_type_ref(t))

    def _make_builtin_type_ref(self, t):
        rec = builtin_ref_t(t.full_name)
        return self._ref_registry.register_object(rec)  # expected fail for duplicates; todo: move ref to Type


def map_type_module_to_refs(buildin_types_registry, ref_registry, local_type_module_registry, module):
    local_name_dict = {}  # name -> ref
    for import_ in module.import_list:
        imported_module = local_type_module_registry.resolve(import_.module_name)
        local_name_dict[import_.name] = imported_module.resolve(import_.name)
    local_type_module = LocalTypeModule()
    mapper = TypeModuleToRefsMapper(buildin_types_registry, ref_registry, local_name_dict)
    for typedef in module.typedefs:
        t = mapper.map(typedef.type)
        rec = meta_ref_t(
            name=typedef.name,
            random_salt=uuid.uuid4().bytes,
            type=t,
            )
        ref = ref_registry.register_object(rec)
        local_type_module.register(typedef.name, ref)
        local_name_dict[typedef.name] = ref
    return local_type_module

def resolve_type_module(types, module):
    assert isinstance(types, TypeNamespace), repr(types)
    meta_type_registry = make_meta_type_registry()
    imports_namespace = TypeNamespace()
    for imp in module.import_list:
        imports_namespace[imp.name] = types[imp.module_name][imp.name]
    module_namespace = TypeNamespace()
    resolver = TypeNameResolver([module_namespace, imports_namespace, types.builtins])
    for typedef in module.typedefs:
        full_name = [module.module_name, typedef.name]
        t = meta_type_registry.resolve(resolver, typedef.type, full_name)
        module_namespace[typedef.name] = t
    return module_namespace
