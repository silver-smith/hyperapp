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
from .meta_association import meta_association, meta_association_def
from .python_module import import_rec_t, python_module_t, import_rec_def_t, python_module_def_t
from .meta_type import list_mt
from .pyobj_association import python_object_association_t, python_object_association_def_t
from .legacy_type import legacy_type_t

log = logging.getLogger(__name__)


primitive_list_types = {}  # primitive t -> list t

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
    meta_association,
    meta_association_def,
    python_object_association_t,
    python_object_association_def_t,
    import_rec_t,
    python_module_t,
    import_rec_def_t,
    python_module_def_t,
    legacy_type_t,
    ]


def register_builtin_types(builtin_types, mosaic, types):
    for t in _builtin_type_list:
        type_ref = builtin_types.register(mosaic, types, t)
    # Register list of builtin types
    for element_t in _builtin_type_list:
        element_ref = types.reverse_resolve(element_t)
        piece = list_mt(element_ref)
        type_ref = mosaic.put(piece)
        t = types.resolve(type_ref)
        primitive_list_types[element_t] = t
        log.debug("Registered builtin list type: %s -> %s", type_ref, t)
