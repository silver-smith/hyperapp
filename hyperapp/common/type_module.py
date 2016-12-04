from .htypes import (
    tString,
    Field,
    TRecord,
    TList,
    tMetaType,
    tTypeDef,
    tTypeModule,
    TypeRegistry,
    TypeResolver,
    )
from .packet_coders import packet_coders
from .type_module_parser import parse_type_module


TYPEDEF_MODULE_ENCODING = 'yaml'



tFileContents = TList(tTypeDef)

def load_typedefs_from_yaml_file( fpath ):
    with open(fpath, 'rb') as f:
        contents = f.read()
    return packet_coders.decode(TYPEDEF_MODULE_ENCODING, contents, tFileContents)

def resolve_typedefs( meta_registry, name_resolver, typedefs ):
    assert isinstance(name_resolver, TypeResolver), repr(name_resolver)
    resolved_registry = TypeRegistry()
    resolver = TypeResolver([resolved_registry], next=name_resolver)
    for typedef in typedefs:
        t = meta_registry.resolve(resolver, typedef.type)
        resolved_registry.register(typedef.name, t)
    return resolved_registry

def resolve_typedefs_from_yaml_file( meta_registry, name_resolver, fpath ):
    typedefs = load_typedefs_from_yaml_file(fpath)
    return resolve_typedefs(meta_registry, name_resolver, typedefs)

def load_types_file( meta_registry, type_registry_registry, fpath ):
    with open(fpath, 'r') as f:
        contents = f.read()
    used_modules, typedefs, loaded_types = parse_type_module(meta_registry, type_registry_registry, fpath, contents)
    return (used_modules, typedefs, loaded_types)

def load_module_from_types_file( meta_registry, type_registry_registry, fpath ):
    used_modules, typedefs, loaded_types = load_types_file(meta_registry, type_registry_registry, fpath)
    module = TypeModule()
    for name, t in loaded_types.items():
        module._add_type(name, t)
    return module
