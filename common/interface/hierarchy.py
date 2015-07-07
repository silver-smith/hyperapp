from .. util import is_list_inst
from . types import join_path, Type, Field


class Class(object):

    def __init__( self, id ):
        self._class_id = id


class TClass(object):

    def __init__( self, id, fields, cls ):
        self.id = id
        self.fields = fields  # Field list
        self.cls = cls  # class to instantiate or None

    def register_class( self, cls ):
        self.cls = cls

    def get_fields( self ):
        return self.fields

    def _validate( self, path, obj ):
        for field in self.fields:
            if not hasattr(obj, field.name):
                raise TypeError('%s: %s' % (path, 'Missing field: %s' % field.name))
            field.validate(path, getattr(rec, field.name))

    def _adopt_args( self, args, kw ):
        return TRecord(self.fields).adopt_args('<Class %s>' % self.id, args, kw)

    def instantiate( self, *args, **kw ):
        fields = self._adopt_args(args, kw)
        if self.cls:
            return self.cls(**fields)
        else:
            rec = Class(self.id)
            for name, val in fields.items():
                setattr(rec, name, val)
            return rec

    # only to be used as base for usual classes
    def make_class( self ):
        tclass = self
        class Class(object):
            def __init__( self, *args, **kw ):
                self._class_id = tclass.id
                for name, val in tclass._adopt_args(args, kw).items():
                    setattr(self, name, val)
        return Class
            

class THierarchy(Type):

    def __init__( self ):
        Type.__init__(self)
        self.registry = {}  # id -> TClass

    def register( self, id, fields=None, cls=None, base=None ):
        assert isinstance(id, basestring), repr(id)
        assert is_list_inst(fields, Field), repr(fields)
        assert id not in self.registry, 'Class id is already registered: %r' % id
        if fields is None:
            fields = []
        if base:
            info = self.resolve(base)
            fields = info.fields + fields
        tclass = TClass(id, fields, cls)
        self.registry[id] = tclass
        return tclass

    def validate( self, path, obj ):
        assert hasattr(obj, '_class_id'), repr(obj)  # not a TClass instance
        self.resolve(obj._class_id)._validate(path, obj)

    def resolve( self, id ):
        assert isinstance(id, basestring), repr(id)
        assert id in self.registry, 'Unknown class id: %r. Known are: %r' % (id, sorted(self.registry.keys()))
        return self.registry[id]
