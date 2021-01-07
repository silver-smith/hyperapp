from .htypes import (
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    )
from .embedded import (
    tEmbedded,
    )
from .builtins import (
    tServerRoutes,
    tIfaceId,
    tPath,
    tUrl,
    )
from .hyper_ref import (
    ref_t,
    capsule_t,
    route_t,
    bundle_t,
    resource_path_t,
    resource_key_t,
    )
from .deduce_value_type import primitive_list_types


_builtin_type_list = [
    # core
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    tEmbedded,
    tServerRoutes,
    tIfaceId,
    tPath,
    tUrl,
    ref_t,
    capsule_t,
    route_t,
    bundle_t,
    resource_path_t,
    resource_key_t,
    ]


builtin_type_names = set(t.name for t in _builtin_type_list)


def register_builtin_types(types):
    for t in _builtin_type_list:
        types.register_builtin_type(t)
    # # Register list of builtin types
    # for t in _builtin_type_list:
    #     type_ref = types.reverse_resolve(t)
    #     list_type_name = f'{t.name}_list'
    #     list_type_rec = meta_ref_t(list_type_name, t_list_meta(t_ref(type_ref)))
    #     list_t = types.register_type(list_type_rec).t
    #     primitive_list_types[t] = list_t
