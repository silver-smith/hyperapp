from .htypes import *
from .namespace import *
from .hierarchy import *
from .embedded import *
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
    registry.register('interface', interface_from_data)
    return registry

def make_builtins_type_namespace():
    namespace = TypeNamespace()
    for t in [
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
        tTypeModule,
        tServerRoutes,
        ]:
        namespace[t.name] = t
    return namespace

def make_root_type_namespace():
    return TypeNamespace(builtins=make_builtins_type_namespace())


def deduce_value_type(value):
    if isinstance(value, (TClassRecord, TExceptionClassRecord)):
        return value._class.hierarchy
    if isinstance(value, Record):
        return value._type
    assert False, 'Add type parameter for values of types others than TRecord or THierarchy'
