from .htypes import (
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    )
from .meta_type import list_mt
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
    # Register list of builtin types
    for element_t in _builtin_type_list:
        element_ref = types.reverse_resolve(element_t)
        piece = list_mt(element_ref)
        t = types.register_type(piece).t
        primitive_list_types[element_t] = t
