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
from .meta_type import list_mt
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
        return primitive_list_types[element_t]  # Use deduce_complex_value_type for non-primitive-element lists.
    raise DeduceTypeError(f"Unable to deduce type for {value!r} (t: {t!r}). Use explicit type parameter.")


def _deduce_list_type(mosaic, types, value):
    element_t = deduce_complex_value_type(mosaic, types, value[0])
    t = TList(element_t)
    try:
        _ = types.reverse_resolve(t)
        return t
    except:
        element_t_ref = types.reverse_resolve(element_t)
        piece = list_mt(element_t_ref)
        type_ref = mosaic.put(piece)
        return types.resolve(type_ref)


def deduce_complex_value_type(mosaic, types, value):
    if isinstance(value, list):
        return _deduce_list_type(mosaic, types, value)
    return deduce_value_type(value)
