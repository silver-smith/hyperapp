from .util import is_list_inst
from .htypes import (
    Type,
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
    ref_t,
    full_type_name_t,
    route_t,
    capsule_t,
    bundle_t,
    )


class BuiltinTypesRegistry(object):

    def __init__(self):
        self._registry = {}  # full name -> Type

    def register(self, full_name, t):
        assert is_list_inst(full_name, str), repr(full_name)
        assert isinstance(t, Type), repr(t)
        self._registry[tuple(full_name)] = t

    def resolve(self, full_name):
        return self._registry.get(tuple(full_name))


def make_builtin_types_registry():
    registry = BuiltinTypesRegistry()
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
        ref_t,
        full_type_name_t,
        route_t,
        capsule_t,
        bundle_t,
        ]:
        registry.register(t.full_name, t)
    return registry
