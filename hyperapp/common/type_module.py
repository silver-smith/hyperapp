from .htypes import (
    tString,
    Field,
    TRecord,
    TList,
    tMetaType,
    tTypeDef,
    tTypeModule,
    TypeRegistry,
    )
from .packet_coders import packet_coders
from .type_module_parser import parse_type_module


TYPEDEF_MODULE_ENCODING = 'yaml'


class TypeModule(object):

    def __init__( self ):
        self._types = {}

    def _add_type( self, name, t ):
        self._types[name] = t
        setattr(self, name, t)


tFileContents = TList(tTypeDef)

def load_typedefs_from_yaml_file( fpath ):
    with open(fpath, 'rb') as f:
        contents = f.read()
    return packet_coders.decode(TYPEDEF_MODULE_ENCODING, contents, tFileContents)

def resolve_typedefs( meta_registry, type_registry, typedefs ):
    loaded_types = TypeRegistry(next=type_registry)
    module = TypeModule()
    for typedef in typedefs:
        t = meta_registry.resolve(loaded_types, typedef.type)
        loaded_types.register(typedef.name, t)
        module._add_type(typedef.name, t)
    return module

def load_typedefs_from_types_file( meta_registry, type_registry, fpath ):
    with open(fpath, 'r') as f:
        contents = f.read()
    typedefs, loaded_types = parse_type_module(meta_registry, type_registry, fpath, contents)
    module = TypeModule()
    for name, t in loaded_types.items():
        module._add_type(name, t)
    return module

def resolve_typedefs_from_yaml_file( meta_registry, type_registry, fpath ):
    typedefs = load_typedefs_from_yaml_file(fpath)
    return resolve_typedefs(meta_registry, type_registry, typedefs)

def resolve_typedefs_from_types_file( meta_registry, type_registry, fpath ):
    typedefs = load_typedefs_from_types_file(fpath)
    return resolve_typedefs(meta_registry, type_registry, typedefs)
