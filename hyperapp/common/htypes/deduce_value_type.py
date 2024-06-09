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


def deduce_value_type(value):
    t = _primitive_types.get(type(value))
    if t:
        return t
    t = getattr(value, '_t', None)
    if isinstance(t, (TRecord, TException)):
        return t
    if isinstance(value, (list, tuple)) and not _is_named_tuple(value):
        if value:
            element_t = deduce_value_type(value[0])
        else:
            element_t = tNone
        try:
            return TList(element_t)
        except KeyError:
            raise DeduceTypeError(
                f"Unable to deduce type for {safe_repr(value)}:"
                f" No list type for: {element_t}. Use explicit type parameter."
            )
    raise DeduceTypeError(f"Unable to deduce type for {safe_repr(value)} (t: {t!r}). Use explicit type parameter.")
