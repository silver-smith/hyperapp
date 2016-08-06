# meta type is type for storing types themselves as data

from .htypes import (
    lbtypes,
    Type,
    TPrimitive,
    tString,
    Field,
    TOptional,
    TRecord,
    TList,
    )
from .hierarchy import THierarchy
from .interface import Interface


tMetaType = THierarchy('type')
tRootMetaType = tMetaType.register('root', fields=[Field('type_id', tString)])

lbtypes.tMetaType = tMetaType
lbtypes.tRootMetaType = tRootMetaType


class TypeRegistry(object):

    def __init__( self ):
        self._registry = {}

    def register( self, type_id, t ):
        assert isinstance(type_id, str), repr(type_id)
        self._registry[type_id] = t

    def resolve( self, rec ):
        assert isinstance(rec, tRootMetaType), repr(rec)
        factory = self._registry.get(rec.type_id)
        assert factory, 'Unknown type_id: %r' % rec.type_id
        return factory(self, rec)


TPrimitive.register_meta()
TOptional.register_meta()
TRecord.register_meta()
TList.register_meta()
THierarchy.register_meta()
Interface.register_meta()
