from .htypes import *
from .namespace import *
from .hierarchy import *
from .embedded import *
from .hyper_ref import *
from .meta_type import*
from .interface import *


def make_meta_type_registry():
    registry = MetaTypeRegistry()
    registry.register('named', named_from_data)
    registry.register('optional', optional_from_data)
    registry.register('list', list_from_data)
    registry.register('record', record_from_data)
    registry.register('hierarchy', hierarchy_from_data)
    registry.register('exception_hierarchy', exception_hierarchy_from_data)
    registry.register('hierarchy_class', hierarchy_class_from_data)
    registry.register('ref', ref_from_data)
    registry.register('interface', interface_from_data)
    return registry

def register_builtin_types(ref_registry, type_resolver):
    for t in [
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
            # meta
            builtin_ref_t,
            meta_ref_t,
            tMetaType,
            ]:
        type_resolver.register_internal_type(ref_registry, t)
