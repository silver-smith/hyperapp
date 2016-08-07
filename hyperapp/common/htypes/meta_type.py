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
from .hierarchy import THierarchy
from .interface import Interface


tMetaType = THierarchy('type')
tRootMetaType = tMetaType.register('root', fields=[Field('type_id', tString)])


tNamed = tMetaType.register('named', base=tRootMetaType, fields=[Field('name', tString)])

def t_named( name ):
    return tNamed(tNamed.id, name)

def named_from_data( type_registry, name_registry, rec ):
    return name_registry.resolve(rec.name)


tOptionalMeta = tMetaType.register(
    'optional', base=tRootMetaType, fields=[Field('base', tMetaType)])

def t_optional_meta( base_t ):
    return tOptionalMeta(tOptionalMeta.id, base_t)

def optional_from_data( type_registry, name_registry, rec ):
    base_t = type_registry.resolve(name_registry, rec.base)
    return TOptional(base_t)


tListMeta = tMetaType.register(
    'list', base=tRootMetaType, fields=[Field('element', tMetaType)])

def t_list_meta( element_t ):
    return tListMeta(tListMeta.id, element_t)

def list_from_data( type_registry, name_registry, rec ):
    element_t = type_registry.resolve(name_registry, rec.element)
    return TList(element_t)


class NameRegistry(object):

    def __init__( self, next=None ):
        assert next is None or isinstance(next, NameRegistry), repr(next)
        self._registry = {}
        self._next = next

    def register( self, name, t ):
        assert isinstance(name, str), repr(name)
        self._registry[name] = t

    def resolve( self, name ):
        assert isinstance(name, str), repr(name)
        t = self._registry.get(name)
        if t is not None:
            return t
        if self._next:
            return self._next.resolve(name)
        raise KeyError('Unknown type name: %r' % name)


class TypeRegistry(object):

    def __init__( self ):
        self._registry = {}

    def register( self, type_id, t ):
        assert isinstance(type_id, str), repr(type_id)
        self._registry[type_id] = t

    def resolve( self, name_registry, rec ):
        assert isinstance(name_registry, NameRegistry), repr(name_registry)
        assert isinstance(rec, tRootMetaType), repr(rec)
        factory = self._registry.get(rec.type_id)
        assert factory, 'Unknown type_id: %r' % rec.type_id
        return factory(self, name_registry, rec)


def make_type_registry():
    registry = TypeRegistry()
    registry.register('named', named_from_data)
    registry.register('optional', optional_from_data)
    registry.register('list', list_from_data)
    return registry

def builtin_type_names():
    registry = NameRegistry()
    for t in [
        tNone,
        tString,
        tBinary,
        tInt,
        tBool,
        tDateTime,
        ]:
        registry.register(t.type_name, t)
    return registry
