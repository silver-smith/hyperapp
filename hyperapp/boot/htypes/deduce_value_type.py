import datetime

from .htypes import (
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    TList,
    )
from .record import TRecord
from .exception import TException
from .meta_type import list_mt


class DeduceTypeError(RuntimeError):
    pass


_primitive_types = {
    type(None): tNone,
    str: tString,
    bytes: tBinary,
    int: tInt,
    bool: tBool,
    datetime.datetime: tDateTime,
    }



def safe_repr(obj):
    try:
        return repr(obj)
    except Exception as x:
        return f"__repr__ failed: {x}"


def _is_named_tuple(value):
    return all(hasattr(value, field) for field in ['_fields', '_field_defaults', '_replace', '_make'])


def _deduce_type(value):
    t = _primitive_types.get(type(value))
    if t:
        return t
    t = getattr(value, '_t', None)
    if isinstance(t, (TRecord, TException)):
        return t
    return None


def deduce_value_type(value):
    t = _deduce_type(value)
    if t is not None:
        return t
    if isinstance(value, (list, tuple)) and not _is_named_tuple(value):
        raise DeduceTypeError(f"Use deduce_value_type_with_list to deduce list types: {safe_repr(value)}.")
    raise DeduceTypeError(f"Unable to deduce type for {safe_repr(value)}. Use explicit type parameter.")


def _deduce_list_type(pyobj_creg, value):
    if value:
        element_t = deduce_value_type_with_list(pyobj_creg, value[0])
    else:
        element_t = tNone  # Does not matter for an empty list.
    # Ensure meta record is added to cache.
    element_t_ref = pyobj_creg.actor_to_ref(element_t)
    piece = list_mt(element_t_ref)
    return pyobj_creg.animate(piece)


def deduce_value_type_with_list(pyobj_creg, value):
    t = _deduce_type(value)
    if t is not None:
        return t
    if isinstance(value, (list, tuple)) and not _is_named_tuple(value):
        return _deduce_list_type(pyobj_creg, value)
    raise DeduceTypeError(f"Unable to deduce type for {safe_repr(value)}. Use explicit type parameter.")
