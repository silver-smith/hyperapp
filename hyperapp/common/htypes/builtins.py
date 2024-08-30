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
from .builtin_service import builtin_service_t
from .code_registry import code_registry_ctr_t
from .attribute import attribute_t, attribute_def_t
from .call import call_t, call_def_t
from .partial import partial_param_t, partial_param_def_t, partial_t, partial_def_t
from .raw import raw_t, raw_def_t

log = logging.getLogger(__name__)


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
    partial_param_t,
    partial_param_def_t,
    partial_t,
    partial_def_t,
    raw_t,
    raw_def_t,
    ]


def register_builtin_types(builtin_types, pyobj_creg):
    for t in _builtin_type_list:
        builtin_types.register(pyobj_creg, t)
