from .htypes import (
    tString,
    Field,
    TRecord,
    TList,
    tMetaType,
    TypeRegistry,
    )
from .packet_coders import packet_coders


TYPEDEF_MODULE_ENCODING = 'yaml'


tTypeDef = TRecord([
    Field('name', tString),
    Field('type', tMetaType),
    ])

tTypeModule = TList(tTypeDef)


class TypeModule(object):

    def __init__( self ):
        self._types = {}

    def _add_type( self, name, t ):
        self._types[name] = t
        setattr(self, name, t)


def load_types_from_yaml_file( fpath ):
    with open(fpath, 'rb') as f:
        data = f.read()
    return packet_coders.decode(TYPEDEF_MODULE_ENCODING, data, tTypeModule)

def resolve_types_from_yaml_file( meta_registry, type_registry, fpath ):
    typedefs = load_types_from_yaml_file(fpath)
    loaded_types = TypeRegistry(next=type_registry)
    module = TypeModule()
    for typedef in typedefs:
        t = meta_registry.resolve(loaded_types, typedef.type)
        loaded_types.register(typedef.name, t)
        module._add_type(typedef.name, t)
    return module
