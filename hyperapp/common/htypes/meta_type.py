# meta type is type for storing types themselves as data

import abc

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
    Field,
    TRecord,
    TList,
    )
from .namespace import TypeNamespace
from .hierarchy import TClass, THierarchy
from .exception_hierarchy import TExceptionHierarchy
from .hyper_ref import ref_t
from .interface import IfaceCommand, Interface


tMetaType = THierarchy('type', name='type')

tRootMetaType = tMetaType.register('root', fields=[
    Field('type_id', tString),
    ])


builtin_ref_t = TRecord('builtin_ref', [
    Field('name', tString),
    ])

meta_ref_t = TRecord('meta_ref', [
    Field('name', tString),
    Field('type', tMetaType),
    ])


tNamed = tMetaType.register('named', base=tRootMetaType, fields=[
    Field('name', tString),
    ])

def t_named(name):
    return tNamed(tNamed.id, name)


ref_type_t = tMetaType.register('ref', base=tRootMetaType, fields=[
    Field('ref', ref_t),
    ])

def t_ref(ref):
    return ref_type_t(ref_type_t.id, ref)

def ref_from_data(meta_type_registry, ref_resolver, rec, name):
    return ref_resolver.resolve(rec, name)


tOptionalMeta = tMetaType.register(
    'optional', base=tRootMetaType, fields=[
        Field('base', tMetaType),
        ])

def t_optional_meta(base_t):
    return tOptionalMeta(tOptionalMeta.id, base_t)

def optional_from_data(meta_type_registry, type_ref_resolver, rec, name):
    base_t = meta_type_registry.resolve(type_ref_resolver, rec.base, name)
    return TOptional(base_t)


tListMeta = tMetaType.register(
    'list', base=tRootMetaType, fields=[
        Field('element', tMetaType),
        ])

def t_list_meta(element_t):
    return tListMeta(tListMeta.id, element_t)

def list_from_data(meta_type_registry, type_ref_resolver, rec, name):
    element_t = meta_type_registry.resolve(type_ref_resolver, rec.element, name)
    return TList(element_t)


tFieldMeta = TRecord('field', [
    Field('name', tString),
    Field('type', tMetaType),
    ])

tRecordMeta = tMetaType.register(
    'record', base=tRootMetaType, fields=[
        Field('base', TOptional(tMetaType)),
        Field('fields', TList(tFieldMeta)),
        ])

def t_field_meta(name, type):
    return tFieldMeta(name, type)

def t_record_meta(fields, base=None):
    assert base is None or isinstance(base, tMetaType), repr(base)
    return tRecordMeta(tRecordMeta.id, base, fields)

def field_from_data(meta_type_registry, type_ref_resolver, rec):
    t = meta_type_registry.resolve(type_ref_resolver, rec.type)
    return Field(rec.name, t)

def field_list_from_data(meta_type_registry, type_ref_resolver, fields):
    return [field_from_data(meta_type_registry, type_ref_resolver, field) for field in fields]

def record_from_data(meta_type_registry, type_ref_resolver, rec, name):
    if rec.base:
        base = meta_type_registry.resolve(type_ref_resolver, rec.base)
        assert isinstance(base, TRecord), (
            'Base for record %s, %s is not a record' % (name, base.name))
    else:
        base = None
    return TRecord(name, field_list_from_data(meta_type_registry, type_ref_resolver, rec.fields), base=base)


tHierarchyMeta = tMetaType.register(
    'hierarchy', base=tRootMetaType, fields=[
        Field('hierarchy_id', tString),
        ])

tExceptionHierarchyMeta = tMetaType.register('exception_hierarchy', base=tHierarchyMeta)

tHierarchyClassMeta = tMetaType.register('hierarchy_class', base=tRootMetaType, fields=[
    Field('hierarchy', tMetaType),  # tNamed is expected
    Field('class_id', tString),
    Field('base', TOptional(tMetaType)),  # tRecordMeta is expected
    Field('fields', TList(tFieldMeta)),
    ])

def t_hierarchy_meta(hierarchy_id):
    return tHierarchyMeta(tHierarchyMeta.id, hierarchy_id)

def t_exception_hierarchy_meta(hierarchy_id):
    return tExceptionHierarchyMeta(tExceptionHierarchyMeta.id, hierarchy_id)

def t_hierarchy_class_meta(hierarchy, class_id, fields, base=None):
    return tHierarchyClassMeta(tHierarchyClassMeta.id, hierarchy, class_id, base, fields)

def hierarchy_from_data(meta_type_registry, type_ref_resolver, rec, name):
    return THierarchy(rec.hierarchy_id, name)

def exception_hierarchy_from_data(meta_type_registry, type_ref_resolver, rec, name):
    return TExceptionHierarchy(rec.hierarchy_id, name)

def hierarchy_class_from_data(meta_type_registry, type_ref_resolver, rec, name):
    hierarchy = meta_type_registry.resolve(type_ref_resolver, rec.hierarchy, name)
    assert isinstance(hierarchy, THierarchy), repr(hierarchy)
    if rec.base is not None:
        base = meta_type_registry.resolve(type_ref_resolver, rec.base, name)
    else:
        base = None
    fields = field_list_from_data(meta_type_registry, type_ref_resolver, rec.fields)
    return hierarchy.register(rec.class_id, base=base, fields=fields)


tIfaceCommandMeta = TRecord('iface_command', [
    Field('request_type', tString),
    Field('command_id', tString),
    Field('params_fields', TList(tFieldMeta)),
    Field('result_fields', TList(tFieldMeta)),
    ])

tInterfaceMeta = tMetaType.register('interface', base=tRootMetaType, fields=[
    Field('base', TOptional(tMetaType)),
    Field('commands', TList(tIfaceCommandMeta)),
    ])


def t_command_meta(request_type, command_id, params_fields, result_fields=None):
    assert request_type in [IfaceCommand.rt_request, IfaceCommand.rt_notification], repr(request_type)
    return tIfaceCommandMeta(request_type, command_id, params_fields, result_fields or [])

def t_interface_meta(commands, base=None):
    return tInterfaceMeta(tInterfaceMeta.id, base, commands)

def command_from_data(meta_type_registry, type_ref_resolver, rec, name):
    params_fields = field_list_from_data(meta_type_registry, type_ref_resolver, rec.params_fields)
    result_fields = field_list_from_data(meta_type_registry, type_ref_resolver, rec.result_fields)
    return IfaceCommand([name, rec.command_id], rec.request_type, rec.command_id, params_fields, result_fields)

def interface_from_data(meta_type_registry, type_ref_resolver, rec, name):
    base_iface = type_ref_resolver.resolve(rec.base) if rec.base else None
    commands = [command_from_data(meta_type_registry, type_ref_resolver, command, name) for command in rec.commands]
    return Interface(name, base_iface, commands)


class TypeRefResolver(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def resolve(self, type_ref, name=None):
        pass


class MetaTypeRegistry(object):

    def __init__(self):
        self._registry = {}

    def register(self, type_id, t):
        assert isinstance(type_id, str), repr(type_id)
        self._registry[type_id] = t

    def resolve(self, type_ref_resolver, rec, name=None):
        assert isinstance(type_ref_resolver, TypeRefResolver), repr(type_ref_resolver)
        assert name is None or type(name) is str, repr(name)
        assert isinstance(rec, tRootMetaType), repr(rec)
        factory = self._registry.get(rec.type_id)
        assert factory, 'Unknown type_id: %r' % rec.type_id
        return factory(self, type_ref_resolver, rec, name)
