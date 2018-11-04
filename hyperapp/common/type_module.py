from .htypes import (
    ref_t,
    TypeNamespace,
    TypeNameResolver,
    make_meta_type_registry,
    )


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
