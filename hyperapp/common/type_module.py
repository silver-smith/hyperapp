from .htypes import (
    TypeNamespace,
    TypeNameResolver,
    make_meta_type_registry,
    tNamed,
    t_ref,
    )
from .mapper import Mapper


class TypeModuleToRefsMapper(Mapper):

    def __init__(self, ref_registry):
        self._ref_registry = ref_registry

    def map_hierarchy_obj(self, tclass, value):
        if tclass is tNamed:
            assert 0
        return value


def map_type_module_to_refs(ref_registry, module):
    mapper = TypeModuleToRefsMapper(ref_registry)
    return mapper.map(module)


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
