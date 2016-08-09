from .htypes import (
    tString,
    Field,
    TRecord,
    TList,
    tMetaType,
    builtin_type_names,
    )
from .packet_coders import packet_coders


TYPEDEF_MODULE_ENCODING = 'yaml'


tTypeDef = TRecord([
    Field('name', tString),
    Field('type', tMetaType),
    ])

tTypeModule = TList(tTypeDef)


def load_types_from_yaml_file( fpath, type_names, meta_types, meta_names_dest ):
    with open(fpath, 'rb') as f:
        data = f.read()
    typedefs = packet_coders.decode(TYPEDEF_MODULE_ENCODING, data, tTypeModule)
    for typedef in typedefs:
        meta_names_dest.register(typedef.name, typedef.type)
