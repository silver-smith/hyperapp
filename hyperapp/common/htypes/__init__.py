from .htypes import *
from .hierarchy import *
from .embedded import *
from .switched import *
from .meta_type import*
from .interface import *
from .list_interface import *


def make_meta_type_registry():
    registry = MetaTypeRegistry()
    registry.register('named', named_from_data)
    registry.register('optional', optional_from_data)
    registry.register('list', list_from_data)
    registry.register('record', record_from_data)
    registry.register('hierarchy', hierarchy_from_data)
    registry.register('exception_hierarchy', exception_hierarchy_from_data)
    registry.register('hierarchy_class', hierarchy_class_from_data)
    registry.register('interface', interface_from_data)
    registry.register('list_interface', list_interface_from_data)
    return registry

def builtin_type_registry():
    registry = TypeRegistry()
    for t in [
        tNone,
        tString,
        tBinary,
        tInt,
        tBool,
        tDateTime,
        ]:
        registry.register(t.type_name, t)
    registry.register('embedded', tEmbedded)
    registry.register('iface_id', tIfaceId)
    registry.register('path', tPath)
    registry.register('url', tUrl)
    registry.register('type_module', tTypeModule)
    registry.register('server_routes', tServerRoutes)
    return registry

def builtin_type_registry_registry(**kw):
    return TypeRegistryRegistry(dict(builtins=builtin_type_registry(), **kw))
