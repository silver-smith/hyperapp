import uuid

from .htypes import (
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


def map_type_module_to_refs(buildin_types_registry, ref_registry, module):
    # leave builtin names as is - they are available on all systems
    local_name_dict = {}  # name -> ref
    mapper = TypeModuleToRefsMapper(buildin_types_registry, ref_registry, local_name_dict)
    for typedef in module.typedefs:
        t = mapper.map(typedef.type)
        rec = meta_ref_t(
            name=typedef.name,
            random_salt=uuid.uuid4().bytes,
            type=t,
            )
        ref = ref_registry.register_object(rec)
        local_name_dict[typedef.name] = ref
        yield (typedef.name, ref)

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
