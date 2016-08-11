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
        data = f.read()
    return packet_coders.decode(TYPEDEF_MODULE_ENCODING, data, tFileContents)

def resolve_typedefs_from_yaml_file( meta_registry, type_registry, fpath ):
    typedefs = load_typedefs_from_yaml_file(fpath)
    loaded_types = TypeRegistry(next=type_registry)
    module = TypeModule()
    for typedef in typedefs:
        t = meta_registry.resolve(loaded_types, typedef.type)
        loaded_types.register(typedef.name, t)
        module._add_type(typedef.name, t)
    return module
