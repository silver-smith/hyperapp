import datetime

from .htypes import tNone, tString, tBinary, tInt, tBool, tDateTime, TList
from .record import TRecord
from .builtins import primitive_list_types


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


def deduce_value_type(value):
    t = _primitive_types.get(type(value))
    if t:
        return t
    t = getattr(value, '_t', None)
    if isinstance(t, TRecord):
        return t
    if isinstance(value, list):
        element_t = deduce_value_type(value[0])
        return primitive_list_types[element_t]  # element_t is expected to be a primitive, KeyError othersize
    raise DeduceTypeError(f"Unable to deduce type for {value!r} (t: {t!r}). Use explicit type parameter.")
