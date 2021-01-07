# meta type is type for storing types themselves as data

import abc
from collections import OrderedDict

from types import SimpleNamespace
from ..util import is_list_inst
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


builtin_t = TRecord('builtin_t', OrderedDict([
    ('name', tString),
    ]))


named_t = TRecord('named_t', OrderedDict([
    ('name', tString),
    ]))


optional_t = TRecord('optional_t', OrderedDict([
    ('base', ref_t),
    ]))


def optional_from_piece(rec, type_code_registry):
    base_t = type_code_registry.invite(rec.base)
    return TOptional(base_t)


# tListMeta = tMetaType.register(
#     'list', base=tRootMetaType, fields=OrderedDict([
#         ('element', tMetaType),
#         ]))

# def t_list_meta(element_t):
#     return tListMeta(tListMeta.id, element_t)

# def list_from_data(meta_type_registry, type_web, rec, name):
#     element_t = meta_type_registry.resolve(type_web, rec.element, name)
#     return TList(element_t)


# tFieldMeta = TRecord('field', OrderedDict([
#     ('name', tString),
#     ('type', tMetaType),
#     ]))

# tRecordMeta = tMetaType.register(
#     'record', base=tRootMetaType, fields=OrderedDict([
#         ('base', TOptional(tMetaType)),
#         ('fields', TList(tFieldMeta)),
#         ]))

# def t_field_meta(name, type):
#     return tFieldMeta(name, type)

# def t_record_meta(fields, base=None):
#     assert base is None or isinstance(base, tMetaType), repr(base)
#     return tRecordMeta(tRecordMeta.id, base, fields)

# def field_from_data(meta_type_registry, type_web, rec):
#     t = meta_type_registry.resolve(type_web, rec.type)
#     return (rec.name, t)

# def field_odict_from_data(meta_type_registry, type_web, fields):
#     return OrderedDict([field_from_data(meta_type_registry, type_web, field) for field in fields])

# def record_from_data(meta_type_registry, type_web, rec, name):
#     if rec.base:
#         base = meta_type_registry.resolve(type_web, rec.base)
#         assert isinstance(base, TRecord), (
#             'Base for record %s, %s is not a record' % (name, base.name))
#     else:
#         base = None
#     return TRecord(name, field_odict_from_data(meta_type_registry, type_web, rec.fields), base=base)


# tHierarchyMeta = tMetaType.register(
#     'hierarchy', base=tRootMetaType, fields=OrderedDict([
#         ('hierarchy_id', tString),
#         ]))

# tExceptionHierarchyMeta = tMetaType.register('exception_hierarchy', base=tHierarchyMeta)

# tHierarchyClassMeta = tMetaType.register('hierarchy_class', base=tRootMetaType, fields=OrderedDict([
#     ('hierarchy', tMetaType),  # tNamed is expected
#     ('class_id', tString),
#     ('base', TOptional(tMetaType)),  # tRecordMeta is expected
#     ('fields', TList(tFieldMeta)),
#     ]))

# def t_hierarchy_meta(hierarchy_id):
#     return tHierarchyMeta(tHierarchyMeta.id, hierarchy_id)

# def t_exception_hierarchy_meta(hierarchy_id):
#     return tExceptionHierarchyMeta(tExceptionHierarchyMeta.id, hierarchy_id)

# def t_hierarchy_class_meta(hierarchy, class_id, fields, base=None):
#     return tHierarchyClassMeta(tHierarchyClassMeta.id, hierarchy, class_id, base, fields)

# def hierarchy_from_data(meta_type_registry, type_web, rec, name):
#     return THierarchy(rec.hierarchy_id, name)

# def exception_hierarchy_from_data(meta_type_registry, type_web, rec, name):
#     return TExceptionHierarchy(rec.hierarchy_id, name)

# def hierarchy_class_from_data(meta_type_registry, type_web, rec, name):
#     hierarchy = meta_type_registry.resolve(type_web, rec.hierarchy, name)
#     assert isinstance(hierarchy, THierarchy), repr(hierarchy)
#     if rec.base is not None:
#         base = meta_type_registry.resolve(type_web, rec.base, name)
#     else:
#         base = None
#     fields = field_odict_from_data(meta_type_registry, type_web, rec.fields)
#     return hierarchy.register(rec.class_id, base=base, fields=fields)


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
    types.register_builtin_type(optional_t)


def register_meta_types(type_code_registry):
    type_code_registry.register_actor(optional_t, optional_from_piece)
