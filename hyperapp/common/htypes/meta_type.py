# meta type is type for storing types themselves as data

from .htypes import (
    Type,
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    TOptional,
    TList,
    )
from .record import TRecord
from .exception import TException
from .hyper_ref import ref_t


builtin_mt = TRecord('builtin_mt', {
    'name': tString,
    })


# Produced by type module parsed, removed by loader.
name_mt = TRecord('name_mt', {
    'name': tString,
    })


name_wrapped_mt = TRecord('name_wrapped_mt', {
    'name': tString,
    'type': ref_t,
    })


def name_wrapped_from_piece(rec, type_code_registry, name):
    return type_code_registry.invite(rec.type, type_code_registry, rec.name)


optional_mt = TRecord('optional_mt', {
    'base': ref_t,
    })


def optional_from_piece(rec, type_code_registry, name, types):
    base_t = types.resolve(rec.base)
    return TOptional(base_t)


list_mt = TRecord('list_mt', {
    'element': ref_t,
    })


def list_from_piece(rec, type_code_registry, name, types):
    element_t = types.resolve(rec.element)
    return TList(element_t)


field_mt = TRecord('field_mt', {
    'name': tString,
    'type': ref_t,
    })

record_mt = TRecord('record_mt', {
    'base': TOptional(ref_t),
    'fields': TList(field_mt),
    })

exception_mt = TRecord('exception_mt', {
    'base': TOptional(ref_t),
    'fields': TList(field_mt),
    })


def _field_from_piece(rec, types):
    t = types.resolve(rec.type)
    return (rec.name, t)


def _field_dict_from_piece_list(field_list, types):
    return dict(_field_from_piece(field, types) for field in field_list)


def record_from_piece(rec, type_code_registry, name, types):
    if rec.base is not None:
        base_t = types.resolve(rec.base)
        assert isinstance(base_t, TRecord), f"Record base is not a record: {base_t}"
    else:
        base_t = None
    field_dict = _field_dict_from_piece_list(rec.fields, types)
    return TRecord(name, field_dict, base=base_t)


def exception_from_piece(rec, type_code_registry, name, types):
    if rec.base is not None:
        base_t = types.resolve(rec.base)
        assert isinstance(base_t, TException), f"Exception base is not an exception: {base_t}"
    else:
        base_t = None
    field_dict = _field_dict_from_piece_list(rec.fields, types)
    return TException(name, field_dict, base=base_t)



def register_builtin_meta_types(builtin_types, mosaic, types):
    builtin_types.register(mosaic, types, name_mt)
    builtin_types.register(mosaic, types, name_wrapped_mt)
    builtin_types.register(mosaic, types, optional_mt)
    builtin_types.register(mosaic, types, list_mt)
    builtin_types.register(mosaic, types, field_mt)
    builtin_types.register(mosaic, types, record_mt)
    builtin_types.register(mosaic, types, exception_mt)


def register_meta_types(mosaic, types, type_code_registry):
    # name_mt does not produce a type, it is removed by type module loader.
    type_code_registry.register_actor(name_wrapped_mt, name_wrapped_from_piece)
    type_code_registry.register_actor(optional_mt, optional_from_piece, types)
    type_code_registry.register_actor(list_mt, list_from_piece, types)
    type_code_registry.register_actor(record_mt, record_from_piece, types)
    type_code_registry.register_actor(exception_mt, exception_from_piece, types)
