import logging

from .htypes import (
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    )
from .hyper_ref import (
    ref_t,
    capsule_t,
    bundle_t,
    )
from .association import association_t
from .python_module import import_rec_t, python_module_t, import_rec_def_t, python_module_def_t
from .meta_type import list_mt
from .pyobj_association import python_object_association_t, python_object_association_def_t
from .legacy_type import legacy_type_t
from .builtin_service import builtin_service_t
from .attribute import attribute_t, attribute_def_t
from .call import call_t, call_def_t

log = logging.getLogger(__name__)


primitive_list_types = {}  # t -> list t
primitive_list_list_types = {}  # t -> list list t

_builtin_type_list = [
    # core
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    ref_t,
    capsule_t,
    bundle_t,
    association_t,
    python_object_association_t,
    python_object_association_def_t,
    import_rec_t,
    python_module_t,
    import_rec_def_t,
    python_module_def_t,
    legacy_type_t,
    builtin_service_t,
    attribute_t,
    attribute_def_t,
    call_t,
    call_def_t,
    ]


def register_builtin_types(builtin_types, mosaic, types):

    def _list_type(element_t):
        element_ref = types.reverse_resolve(element_t)
        piece = list_mt(element_ref)
        type_ref = mosaic.put(piece)
        return types.resolve(type_ref)

    for t in _builtin_type_list:
        type_ref = builtin_types.register(mosaic, types, t)
    # Register list of builtin types
    for element_t in _builtin_type_list:
        list_t = _list_type(element_t)
        list_list_t = _list_type(list_t)
        primitive_list_types[element_t] = list_t
        primitive_list_list_types[element_t] = list_list_t
        log.debug("Registered builtin list type: %s -> %s, %s", type_ref, list_t, list_list_t)
