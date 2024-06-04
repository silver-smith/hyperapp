from hyperapp.common.htypes import (
    Type,
    TOptional,
    TList,
    TRecord,
    TException,
    )

from . import htypes
from .services import (
    pyobj_creg,
    )


def _fields_to_mt(fields):
    return tuple(
        htypes.builtin.field_mt(name, pyobj_creg.actor_to_ref(t))
        for name, t in fields.items()
        )

def _base_to_ref(base):
    if base is None:
        return None
    return pyobj_creg.actor_to_ref(base)


def type_to_piece(t):
    if not isinstance(t, Type):
        return None
    if isinstance(t, TOptional):
        return htypes.builtin.optional_mt(
            base=pyobj_creg.actor_to_ref(t.base_t),
            )
    if isinstance(t, TList):
        return htypes.builtin.list_mt(
            element=pyobj_creg.actor_to_ref(t.element_t),
            )
    if isinstance(t, TRecord):
        return htypes.builtin.record_mt(
            module_name=t.module_name,
            name=t.name,
            base=_base_to_ref(t.base),
            fields=_fields_to_mt(t.fields),
            )
    if isinstance(t, TException):
        return htypes.builtin.exception_mt(
            module_name=t.module_name,
            name=t.name,
            base=_base_to_ref(t.base),
            fields=_fields_to_mt(t.fields),
            )
    raise RuntimeError(f"Reconstructor: Unknown type: {t!r}")
