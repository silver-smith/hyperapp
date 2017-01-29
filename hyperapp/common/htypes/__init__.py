from .htypes import *
from .hierarchy import *
from .switched import *
from .meta_type import*
from .resource_type import *
from .packet import *
from .request import *
from .interface import *
from .list_interface import *


def make_meta_type_registry():
    registry = MetaTypeRegistry()
    registry.register('named', named_from_data)
    registry.register('optional', optional_from_data)
    registry.register('list', list_from_data)
    registry.register('record', record_from_data)
    registry.register('hierarchy', hierarchy_from_data)
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
    registry.register('iface_id', tIfaceId)
    registry.register('path', tPath)
    registry.register('url', tUrl)
    registry.register('requirement', tRequirement)
    registry.register('type_module', tTypeModule)
    registry.register('module', tModule)
    registry.register('resource_id', tResourceId)
    registry.register('resource_list', tResourceList)
    return registry

def builtin_type_registry_registry():
    return TypeRegistryRegistry(dict(builtins=builtin_type_registry()))
