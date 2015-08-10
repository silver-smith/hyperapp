from .. util import is_list_inst
from . types import join_path, Type, Field, TRecord


class Class(object):

    def __init__( self, id ):
        self._class_id = id


class TClass(TRecord):

    def __init__( self, hierarchy, id, base, fields ):
        TRecord.__init__(self, fields)
        self.hierarchy = hierarchy
        self.id = id
        self.base = base

    def get_fields( self ):
        if self.base:
            return self.base.get_fields() + self.fields
        else:
            return self.fields

    def _validate( self, path, obj ):
        for field in self.get_fields():
            if not hasattr(obj, field.name):
                raise TypeError('%s: %s' % (path, 'Missing field: %s' % field.name))
            field.validate(path, getattr(obj, field.name))

    def make_object( self ):
        return Class(self.id)
            

class THierarchy(Type):

    def __init__( self ):
        Type.__init__(self)
        self.registry = {}  # id -> TClass

    def register( self, id, fields=None, base=None ):
        assert isinstance(id, basestring), repr(id)
        assert fields is None or is_list_inst(fields, Field), repr(fields)
        assert base is None or isinstance(base, TClass), repr(base)
        assert id not in self.registry, 'Class id is already registered: %r' % id
        tclass = TClass(self, id, base, fields or [])
        self.registry[id] = tclass
        return tclass

    def validate( self, path, obj ):
        self.resolve_obj(obj)._validate(path, obj)

    def resolve( self, id ):
        assert isinstance(id, basestring), repr(id)
        assert id in self.registry, 'Unknown class id: %r. Known are: %r' % (id, sorted(self.registry.keys()))
        return self.registry[id]

    def resolve_obj( self, obj ):
        assert hasattr(obj, '_class_id'), repr(obj)  # not a TClass instance
        id = obj._class_id
        return self.resolve(id)
