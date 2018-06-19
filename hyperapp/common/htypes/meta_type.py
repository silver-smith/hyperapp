# meta type is type for storing types themselves as data

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
from .hierarchy import TClass, THierarchy, TExceptionHierarchy
from .interface import IfaceCommand, Interface


tMetaType = THierarchy('type', full_name=['meta_type', 'type'])
tRootMetaType = tMetaType.register('root', fields=[Field('type_id', tString)], full_name=['meta_type', 'root'])


tImport = TRecord([
    Field('module_name', tString),
    Field('name', tString),
    ])

tTypeDef = TRecord([
    Field('name', tString),
    Field('type', tMetaType),
    ], full_name=['meta_type', 'typedef'])

tProvidedClass = TRecord([
    Field('hierarchy_id', tString),
    Field('class_id', tString),
    ], full_name=['meta_type', 'provided_class'])

tTypeModule = TRecord([
    Field('module_name', tString),
    Field('import_list', TList(tImport)),
    Field('provided_classes', TList(tProvidedClass)),
    Field('typedefs', TList(tTypeDef)),
    ], full_name=['meta_type', 'type_module'])


tNamed = tMetaType.register('named', base=tRootMetaType, fields=[Field('name', tString)], full_name=['meta_type', 'named'])

def t_named(name):
    return tNamed(tNamed.id, name)

def named_from_data(meta_type_registry, name_resolver, rec, full_name):
    return name_resolver.resolve(rec.name)


tOptionalMeta = tMetaType.register(
    'optional', base=tRootMetaType, fields=[Field('base', tMetaType)], full_name=['meta_type', 'optional'])

def t_optional_meta(base_t):
    return tOptionalMeta(tOptionalMeta.id, base_t)

def optional_from_data(meta_type_registry, name_resolver, rec, full_name):
    base_t = meta_type_registry.resolve(name_resolver, rec.base, full_name)
    return TOptional(base_t)


tListMeta = tMetaType.register(
    'list', base=tRootMetaType, fields=[Field('element', tMetaType)], full_name=['meta_type', 'list'])

def t_list_meta(element_t):
    return tListMeta(tListMeta.id, element_t)

def list_from_data(meta_type_registry, name_resolver, rec, full_name):
    element_t = meta_type_registry.resolve(name_resolver, rec.element, full_name)
    return TList(element_t)


tFieldMeta = TRecord([
    Field('name', tString),
    Field('type', tMetaType),
    ], full_name=['meta_type', 'field'])

tRecordMeta = tMetaType.register(
    'record', base=tRootMetaType, fields=[
        Field('base', TOptional(tMetaType)),
        Field('fields', TList(tFieldMeta)),
        ], full_name=['meta_type', 'record'])

def t_field_meta(name, type):
    return tFieldMeta(name, type)

def t_record_meta(fields, base=None):
    assert base is None or isinstance(base, tMetaType), repr(base)
    return tRecordMeta(tRecordMeta.id, base, fields)

def field_from_data(meta_type_registry, name_resolver, rec):
    t = meta_type_registry.resolve(name_resolver, rec.type)
    return Field(rec.name, t)

def field_list_from_data(meta_type_registry, name_resolver, fields):
    return [field_from_data(meta_type_registry, name_resolver, field) for field in fields]

def record_from_data(meta_type_registry, name_resolver, rec, full_name):
    if rec.base:
        base = meta_type_registry.resolve(name_resolver, rec.base)
        assert isinstance(base, TRecord), (
            'Base for record %s, %s is not a record' % ('.'.join(full_name), '.'.join(base.full_name)))
    else:
        base = None
    return TRecord(field_list_from_data(meta_type_registry, name_resolver, rec.fields), base=base, full_name=full_name)


tHierarchyMeta = tMetaType.register(
    'hierarchy', base=tRootMetaType, fields=[Field('hierarchy_id', tString)], full_name=['meta_type', 'hierarchy'])

tExceptionHierarchyMeta = tMetaType.register('exception_hierarchy', base=tHierarchyMeta, full_name=['meta_type', 'exception_hierarchy'])

tHierarchyClassMeta = tMetaType.register('hierarchy_class', base=tRootMetaType, fields=[
    Field('hierarchy', tMetaType),  # tNamed is expected
    Field('class_id', tString),
    Field('base', TOptional(tMetaType)),  # tRecordMeta is expected
    Field('fields', TList(tFieldMeta)),
    ], full_name=['meta_type', 'hierarchy_class'])

def t_hierarchy_meta(hierarchy_id):
    return tHierarchyMeta(tHierarchyMeta.id, hierarchy_id)

def t_exception_hierarchy_meta(hierarchy_id):
    return tExceptionHierarchyMeta(tExceptionHierarchyMeta.id, hierarchy_id)

def t_hierarchy_class_meta(hierarchy_name, class_id, base_name, fields):
    return tHierarchyClassMeta(tHierarchyClassMeta.id,
                               t_named(hierarchy_name), class_id,
                               t_named(base_name) if base_name else None, fields)

def hierarchy_from_data(meta_type_registry, name_resolver, rec, full_name):
    return THierarchy(rec.hierarchy_id, full_name)

def exception_hierarchy_from_data(meta_type_registry, name_resolver, rec, full_name):
    return TExceptionHierarchy(rec.hierarchy_id, full_name)

def hierarchy_class_from_data(meta_type_registry, name_resolver, rec, full_name):
    hierarchy = meta_type_registry.resolve(name_resolver, rec.hierarchy, full_name)
    assert isinstance(hierarchy, THierarchy), repr(hierarchy)
    if rec.base is not None:
        base = meta_type_registry.resolve(name_resolver, rec.base, full_name)
    else:
        base = None
    fields = field_list_from_data(meta_type_registry, name_resolver, rec.fields)
    return hierarchy.register(rec.class_id, base=base, fields=fields, full_name=full_name)


tIfaceCommandMeta = TRecord([
    Field('request_type', tString),
    Field('command_id', tString),
    Field('params_fields', TList(tFieldMeta)),
    Field('result_fields', TList(tFieldMeta)),
    ], full_name=['meta_type', 'iface_command'])

tInterfaceMeta = tMetaType.register('interface', base=tRootMetaType, fields=[
    Field('base_iface_name', TOptional(tString)),
    Field('commands', TList(tIfaceCommandMeta)),
    ], full_name=['meta_type', 'interface'])


def t_command_meta(request_type, command_id, params_fields, result_fields=None):
    assert request_type in [IfaceCommand.rt_request, IfaceCommand.rt_notification], repr(request_type)
    return tIfaceCommandMeta(request_type, command_id, params_fields, result_fields or [])

def t_interface_meta(base_iface_name, commands):
    return tInterfaceMeta(tInterfaceMeta.id, base_iface_name, commands)

def command_from_data(meta_type_registry, name_resolver, rec, full_name):
    params_fields = field_list_from_data(meta_type_registry, name_resolver, rec.params_fields)
    result_fields = field_list_from_data(meta_type_registry, name_resolver, rec.result_fields)
    return IfaceCommand(full_name + [rec.command_id], rec.request_type, rec.command_id, params_fields, result_fields)

def interface_from_data(meta_type_registry, name_resolver, rec, full_name):
    base_iface = name_resolver.resolve(rec.base_iface_name) if rec.base_iface_name else None
    commands = [command_from_data(meta_type_registry, name_resolver, command, full_name) for command in rec.commands]
    return Interface(full_name, base_iface, commands)


class MetaTypeRegistry(object):

    def __init__(self):
        self._registry = {}

    def register(self, type_id, t):
        assert isinstance(type_id, str), repr(type_id)
        self._registry[type_id] = t

    def resolve(self, name_resolver, rec, full_name=None):
        assert isinstance(name_resolver, TypeNameResolver), repr(name_resolver)
        assert full_name is None or is_list_inst(full_name, str), repr(full_name)
        assert isinstance(rec, tRootMetaType), repr(rec)
        factory = self._registry.get(rec.type_id)
        assert factory, 'Unknown type_id: %r' % rec.type_id
        return factory(self, name_resolver, rec, full_name)


class UnknownTypeError(KeyError):

    def __init__(self, name):
        KeyError.__init__(self, 'Unknown type: %r' % name)
        self.name = name


class TypeNameResolver(object):

    def __init__(self, type_namespace_list):
        assert type_namespace_list is None or is_list_inst(type_namespace_list, TypeNamespace), repr(type_namespace_list)
        self._type_namespace_list = type_namespace_list or []

    def resolve(self, name):
        for namespace in self._type_namespace_list:
            value = namespace.get(name)
            if value is not None:
                return value
        raise UnknownTypeError(name)
