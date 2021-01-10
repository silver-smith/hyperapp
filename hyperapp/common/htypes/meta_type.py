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
from .hyper_ref import ref_t
from .interface import Request, Notification, Interface


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


def optional_from_piece(rec, type_code_registry, name):
    base_t = type_code_registry.invite(rec.base, type_code_registry, None)
    return TOptional(base_t)


list_mt = TRecord('list_mt', {
    'element': ref_t,
    })


def list_from_piece(rec, type_code_registry, name):
    element_t = type_code_registry.invite(rec.element, type_code_registry, None)
    return TList(element_t)


field_mt = TRecord('field_mt', {
    'name': tString,
    'type': ref_t,
    })

record_mt = TRecord('record_mt', {
    'base': TOptional(ref_t),
    'fields': TList(field_mt),
    })


def _field_from_piece(rec, type_code_registry):
    t = type_code_registry.invite(rec.type, type_code_registry, None)
    return (rec.name, t)


def _field_dict_from_piece_list(field_list, type_code_registry):
    return dict(_field_from_piece(field, type_code_registry) for field in field_list)


def record_from_piece(rec, type_code_registry, name):
    if rec.base is not None:
        base_t = type_code_registry.invite(rec.base, type_code_registry, None)
        assert isinstance(base_t, TRecord), f"Record base is not a record: {base_t}"
    else:
        base_t = None
    field_dict = _field_dict_from_piece_list(rec.fields, type_code_registry)
    return TRecord(name, field_dict, base=base_t)


request_mt = TRecord('request_mt', {
    'method_name': tString,
    'param_fields': TList(field_mt),
    'response_fields': TList(field_mt),
    })

notification_mt = TRecord('notification_mt', {
    'method_name': tString,
    'param_fields': TList(field_mt),
    })

method_field_mt = TRecord('field_mt', {
    'name': tString,
    'method': ref_t,
    })

interface_mt = TRecord('interface_mt', {
    'base': TOptional(ref_t),
    'method_list': TList(method_field_mt),
    })


def request_from_piece(piece, type_code_registry, name):
    param_field_dict = _field_dict_from_piece_list(piece.param_fields, type_code_registry)
    response_field_dict = _field_dict_from_piece_list(piece.response_fields, type_code_registry)
    params_record_t = TRecord(f'{name}_params', param_field_dict)
    response_record_t = TRecord(f'{name}_response', response_field_dict)
    return Request(piece.method_name, params_record_t, response_record_t)


def notification_from_piece(piece, type_code_registry, name):
    param_field_dict = _field_dict_from_piece_list(piece.param_fields, type_code_registry)
    params_record_t = TRecord(f'{name}_params', param_field_dict)
    return Notification(piece.method_name, params_record_t)


def _method_iter_from_field_list(method_field_list, type_code_registry, name):
    for field in method_field_list:
        yield type_code_registry.invite(field.method, type_code_registry, f'{name}_{field.name}')


def interface_from_piece(piece, type_code_registry, name):
    if piece.base is not None:
        base_t = type_code_registry.invite(piece.base, type_code_registry, None)
        assert isinstance(base_t, Interface), f"Interface base is not a Interface: {base_t}"
    else:
        base_t = None
    method_list = list(_method_iter_from_field_list(piece.method_list, type_code_registry, name))
    return Interface(name, base_t, method_list)


def register_builtin_meta_types(types):
    types.register_builtin_type(name_mt)
    types.register_builtin_type(name_wrapped_mt)
    types.register_builtin_type(optional_mt)
    types.register_builtin_type(list_mt)
    types.register_builtin_type(field_mt)
    types.register_builtin_type(record_mt)
    types.register_builtin_type(request_mt)
    types.register_builtin_type(notification_mt)
    types.register_builtin_type(interface_mt)


def register_meta_types(type_code_registry):
    # name_mt does not produce a type, it is removed by type module loader.
    type_code_registry.register_actor(name_wrapped_mt, name_wrapped_from_piece)
    type_code_registry.register_actor(optional_mt, optional_from_piece)
    type_code_registry.register_actor(list_mt, list_from_piece)
    type_code_registry.register_actor(record_mt, record_from_piece)
    type_code_registry.register_actor(request_mt, request_from_piece)
    type_code_registry.register_actor(notification_mt, notification_from_piece)
    type_code_registry.register_actor(interface_mt, interface_from_piece)
