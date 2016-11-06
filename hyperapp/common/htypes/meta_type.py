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
    Field,
    TRecord,
    TList,
    )
from .hierarchy import TClass, THierarchy
from .interface import tHandle, tObject, tBaseObject, IfaceCommand, Interface


tMetaType = THierarchy('type')
tRootMetaType = tMetaType.register('root', fields=[Field('type_id', tString)])


tProvidedClass = TRecord([
    Field('hierarchy_id', tString),
    Field('class_id', tString),
    ])

tTypeDef = TRecord([
    Field('name', tString),
    Field('type', tMetaType),
    ])

tTypeModule = TRecord([
    Field('module_name', tString),
    Field('provided_classes', TList(tProvidedClass)),
    Field('typedefs', TList(tTypeDef)),
    ])


tNamed = tMetaType.register('named', base=tRootMetaType, fields=[Field('name', tString)])

def t_named( name ):
    return tNamed(tNamed.id, name)

def named_from_data( meta_registry, type_registry, rec ):
    return type_registry.resolve(rec.name)


tOptionalMeta = tMetaType.register(
    'optional', base=tRootMetaType, fields=[Field('base', tMetaType)])

def t_optional_meta( base_t ):
    return tOptionalMeta(tOptionalMeta.id, base_t)

def optional_from_data( meta_registry, type_registry, rec ):
    base_t = meta_registry.resolve(type_registry, rec.base)
    return TOptional(base_t)


tListMeta = tMetaType.register(
    'list', base=tRootMetaType, fields=[Field('element', tMetaType)])

def t_list_meta( element_t ):
    return tListMeta(tListMeta.id, element_t)

def list_from_data( meta_registry, type_registry, rec ):
    element_t = meta_registry.resolve(type_registry, rec.element)
    return TList(element_t)


tFieldMeta = TRecord([
    Field('name', tString),
    Field('type', tMetaType),
    ])

tRecordMeta = tMetaType.register(
    'record', base=tRootMetaType, fields=[Field('fields', TList(tFieldMeta))])

def t_field_meta( name, type ):
    return tFieldMeta(name, type)

def t_record_meta( fields ):
    return tRecordMeta(tRecordMeta.id, fields)

def field_from_data( meta_registry, type_registry, rec ):
    t = meta_registry.resolve(type_registry, rec.type)
    return Field(rec.name, t)

def field_list_from_data( meta_registry, type_registry, fields ):
    return [field_from_data(meta_registry, type_registry, field) for field in fields]

def record_from_data( meta_registry, type_registry, rec ):
    return TRecord(field_list_from_data(meta_registry, type_registry, rec.fields))


tHierarchyMeta = tMetaType.register(
    'hierarchy', base=tRootMetaType, fields=[Field('hierarchy_id', tString)])

tHierarchyClassMeta = tMetaType.register('hierarchy_class', base=tRootMetaType, fields=[
    Field('hierarchy', tMetaType),  # tNamed is expected
    Field('class_id', tString),
    Field('base', TOptional(tMetaType)),  # tRecordMeta is expected
    Field('fields', TList(tFieldMeta)),
    ])

def t_hierarchy_meta( hierarchy_id ):
    return tHierarchyMeta(tHierarchyMeta.id, hierarchy_id)

def t_hierarchy_class_meta( hierarchy_name, class_id, base_name, fields ):
    return tHierarchyClassMeta(tHierarchyClassMeta.id,
                               t_named(hierarchy_name), class_id,
                               t_named(base_name) if base_name else None, fields)

def hierarchy_from_data( meta_registry, type_registry, rec ):
    return THierarchy(rec.hierarchy_id)

def hierarchy_class_from_data( meta_registry, type_registry, rec ):
    hierarchy = meta_registry.resolve(type_registry, rec.hierarchy)
    assert isinstance(hierarchy, THierarchy), repr(hierarchy)
    if rec.base is not None:
        base = meta_registry.resolve(type_registry, rec.base)
    else:
        base = None
    fields = field_list_from_data(meta_registry, type_registry, rec.fields)
    return hierarchy.register(rec.class_id, base=base, fields=fields)


tIfaceCommandMeta = TRecord([
    Field('request_type', tString),
    Field('command_id', tString),
    Field('params_fields', TList(tFieldMeta)),
    Field('result_fields', TList(tFieldMeta)),
    ])

tInterfaceMeta = tMetaType.register('interface', base=tRootMetaType, fields=[
    Field('iface_id', tString),
    Field('contents_fields', TList(tFieldMeta)),
    Field('diff_type', TOptional(tMetaType)),
    Field('commands', TList(tIfaceCommandMeta)),
    ])


def t_command_meta( request_type, command_id, params_fields, result_fields=None ):
    assert request_type in [IfaceCommand.rt_request, IfaceCommand.rt_notification], repr(request_type)
    return tIfaceCommandMeta(request_type, command_id, params_fields, result_fields or [])

def t_interface_meta( iface_id, commands, contents_fields=None, diff_type=None ):
    return tInterfaceMeta(tInterfaceMeta.id, iface_id, contents_fields or [], diff_type, commands)

def command_from_data( meta_registry, type_registry, rec ):
    params_fields = field_list_from_data(meta_registry, type_registry, rec.params_fields)
    result_fields = field_list_from_data(meta_registry, type_registry, rec.result_fields)
    return IfaceCommand(rec.request_type, rec.command_id, params_fields, result_fields)

def interface_from_data( meta_registry, type_registry, rec ):
    contents_fields = field_list_from_data(meta_registry, type_registry, rec.contents_fields)
    diff_type = meta_registry.resolve(type_registry, rec.diff_type)  if rec.diff_type is not None else None
    commands = [command_from_data(meta_registry, type_registry, command) for command in rec.commands]
    return Interface(rec.iface_id, contents_fields=contents_fields, diff_type=diff_type, commands=commands)


class TypeRegistry(object):

    def __init__( self, next=None ):
        assert next is None or isinstance(next, TypeRegistry), repr(next)
        self._registry = {}
        self._next = next

    def register( self, name, t ):
        assert isinstance(name, str), repr(name)
        assert isinstance(t, (Type, Interface)), repr(t)
        self._registry[name] = t

    def has_name( self, name ):
        if name in self._registry: return True
        if self._next:
            return self._next.has_name(name)
        return False

    def get_name( self, name ):
        if name in self._registry:
            return self._registry[name]
        if self._next:
            return self._next.get_name(name)
        return None

    def items( self ):
        return self._registry.items()

    def resolve( self, name ):
        assert isinstance(name, str), repr(name)
        t = self._registry.get(name)
        if t is not None:
            return t
        if self._next:
            return self._next.resolve(name)
        raise KeyError('Unknown type name: %r' % name)


class MetaTypeRegistry(object):

    def __init__( self ):
        self._registry = {}

    def register( self, type_id, t ):
        assert isinstance(type_id, str), repr(type_id)
        self._registry[type_id] = t

    def resolve( self, type_registry, rec ):
        assert isinstance(type_registry, TypeRegistry), repr(type_registry)
        assert isinstance(rec, tRootMetaType), repr(rec)
        factory = self._registry.get(rec.type_id)
        assert factory, 'Unknown type_id: %r' % rec.type_id
        return factory(self, type_registry, rec)
