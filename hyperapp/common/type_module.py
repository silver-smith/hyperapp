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


def load_types_from_yaml_file( meta_registry, type_registry, fpath ):
    with open(fpath, 'rb') as f:
        data = f.read()
    typedefs = packet_coders.decode(TYPEDEF_MODULE_ENCODING, data, tTypeModule)
    loaded_types = TypeRegistry(next=type_registry)
    for typedef in typedefs:
        t = meta_registry.resolve(loaded_types, typedef.type)
        loaded_types.register(typedef.name, t)
    return loaded_types
