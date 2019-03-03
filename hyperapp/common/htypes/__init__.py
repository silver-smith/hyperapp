from .htypes import *
from .namespace import *
from .hierarchy import *
from .exception_hierarchy import *
from .embedded import *
from .hyper_ref import *
from .meta_type import*
from .interface import *


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
    tIfaceId,
    tPath,
    tUrl,
    tServerRoutes,
    ref_t,
    route_t,
    capsule_t,
    bundle_t,
    resource_path_t,
    resource_key_t,
    # meta
    tMetaType,
    ]

builtin_type_names = set(t.name for t in _builtin_type_list)


def register_builtin_types(ref_registry, type_resolver):
    for t in _builtin_type_list:
        type_resolver.register_builtin_type(ref_registry, t)
