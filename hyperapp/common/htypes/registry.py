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
from .meta_type import (
    tMetaType,
    MetaTypeRegistry,
    meta_ref_t,
    t_ref,
    t_list_meta,
    optional_from_data,
    list_from_data,
    record_from_data,
    hierarchy_from_data,
    exception_hierarchy_from_data,
    hierarchy_class_from_data,
    ref_from_data,
    interface_from_data,
    )
from .deduce_value_type import primitive_list_types


def make_meta_type_registry():
    registry = MetaTypeRegistry()
    registry.register('optional', optional_from_data)
    registry.register('list', list_from_data)
    registry.register('record', record_from_data)
    registry.register('hierarchy', hierarchy_from_data)
    registry.register('exception_hierarchy', exception_hierarchy_from_data)
    registry.register('hierarchy_class', hierarchy_class_from_data)
    registry.register('ref', ref_from_data)
    registry.register('interface', interface_from_data)
    return registry


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
    # meta
    tMetaType,
    ]


builtin_type_names = set(t.name for t in _builtin_type_list)


def register_builtin_types(mosaic, types):
    for t in _builtin_type_list:
        types.register_builtin_type(mosaic, t)
    # Register list of builtin types
    for t in _builtin_type_list:
        type_ref = types.reverse_resolve(t)
        list_type_name = f'{t.name}_list'
        list_type_rec = meta_ref_t(list_type_name, t_list_meta(t_ref(type_ref)))
        list_t = types.register_type(mosaic, list_type_rec).t
        primitive_list_types[t] = list_t
