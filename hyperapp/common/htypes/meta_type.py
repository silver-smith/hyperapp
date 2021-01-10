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
from .interface import IfaceCommand, Interface


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


def field_from_piece(rec, type_code_registry):
    t = type_code_registry.invite(rec.type, type_code_registry, None)
    return (rec.name, t)


def field_dict_from_piece_list(field_list, type_code_registry):
    return dict(field_from_piece(field, type_code_registry) for field in field_list)


def record_from_piece(rec, type_code_registry, name):
    if rec.base is not None:
        base_t = type_code_registry.invite(rec.base, type_code_registry, None)
        assert isinstance(base_t, TRecord), f"Record base is not a record: {base_t}"
    else:
        base_t = None
    field_dict = field_dict_from_piece_list(rec.fields, type_code_registry)
    return TRecord(name, field_dict, base=base_t)


# tIfaceCommandMeta = TRecord('iface_command', OrderedDict([
#     ('request_type', tString),
#     ('command_id', tString),
#     ('params_fields', TList(tFieldMeta)),
#     ('result_fields', TList(tFieldMeta)),
#     ]))

# tInterfaceMeta = tMetaType.register('interface', base=tRootMetaType, fields=OrderedDict([
#     ('base', TOptional(tMetaType)),
#     ('commands', TList(tIfaceCommandMeta)),
#     ]))


# def t_command_meta(request_type, command_id, params_fields, result_fields=None):
#     assert request_type in [IfaceCommand.rt_request, IfaceCommand.rt_notification], repr(request_type)
#     return tIfaceCommandMeta(request_type, command_id, params_fields, result_fields or [])

# def t_interface_meta(commands, base=None):
#     return tInterfaceMeta(tInterfaceMeta.id, base, commands)

# def command_from_data(meta_type_registry, type_web, rec, name):
#     params_fields = field_odict_from_data(meta_type_registry, type_web, rec.params_fields)
#     result_fields = field_odict_from_data(meta_type_registry, type_web, rec.result_fields)
#     return IfaceCommand([name, rec.command_id], rec.request_type, rec.command_id, params_fields, result_fields)

# def interface_from_data(meta_type_registry, type_web, rec, name):
#     base_iface = type_web.resolve(rec.base) if rec.base else None
#     commands = [command_from_data(meta_type_registry, type_web, command, name) for command in rec.commands]
#     return Interface(name, base_iface, commands)


def register_builtin_meta_types(types):
    types.register_builtin_type(name_mt)
    types.register_builtin_type(name_wrapped_mt)
    types.register_builtin_type(optional_mt)
    types.register_builtin_type(list_mt)
    types.register_builtin_type(field_mt)
    types.register_builtin_type(record_mt)


def register_meta_types(type_code_registry):
    # name_mt does not produce a type, it is removed by type module loader.
    type_code_registry.register_actor(name_wrapped_mt, name_wrapped_from_piece)
    type_code_registry.register_actor(optional_mt, optional_from_piece)
    type_code_registry.register_actor(list_mt, list_from_piece)
    type_code_registry.register_actor(record_mt, record_from_piece)
