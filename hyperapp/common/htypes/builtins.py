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
from .builtin_service import builtin_service_t
from .code_registry import code_registry_ctr_t
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
    import_rec_t,
    python_module_t,
    import_rec_def_t,
    python_module_def_t,
    builtin_service_t,
    code_registry_ctr_t,
    attribute_t,
    attribute_def_t,
    call_t,
    call_def_t,
    ]


def register_builtin_types(builtin_types, mosaic, pyobj_creg):

    def _list_type(element_t):
        element_piece = pyobj_creg.reverse_resolve(element_t)
        element_ref = mosaic.put(element_piece)
        list_piece = list_mt(element_ref)
        return pyobj_creg.animate(list_piece)

    for t in _builtin_type_list:
        builtin_types.register(pyobj_creg, t)
    # Register list of builtin types
    for element_t in _builtin_type_list:
        list_t = _list_type(element_t)
        list_list_t = _list_type(list_t)
        primitive_list_types[element_t] = list_t
        primitive_list_list_types[element_t] = list_list_t
        log.debug("Registered builtin list type: %s -> %s, %s", element_t, list_t, list_list_t)
