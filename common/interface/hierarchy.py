from .. util import is_list_inst
from . types import join_path, Type, Field, TRecord


class Class(object):

    def __init__( self, id ):
        self._class_id = id


class TClass(object):

    def __init__( self, hierarchy, id, base, fields, cls ):
        self.hierarchy = hierarchy
        self.id = id
        self.base = base
        self.fields = fields  # Field list
        self.cls = cls  # class to instantiate or None

    def register_class( self, cls ):
        self.cls = cls
        self.hierarchy.cls2id[cls] = self.id

    def get_class( self ):
        if self.cls:
            return self.cls
        if self.base:
            return self.base.get_class()
        return None

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

    def _adopt_args( self, args, kw ):
        return TRecord(self.get_fields()).adopt_args('<Class %s>' % self.id, args, kw)

    def instantiate( self, *args, **kw ):
        fields = self._adopt_args(args, kw)
        cls = self.get_class()
        if cls:
            return cls(**fields)
        else:
            rec = Class(self.id)
            for name, val in fields.items():
                setattr(rec, name, val)
            return rec

    # only to be used as base for usual classes
    def make_class( self ):
        tclass = self
        class ClassBase(object):
            def __init__( self, *args, **kw ):
                self._class_id = tclass.id
                for name, val in tclass._adopt_args(args, kw).items():
                    setattr(self, name, val)
        return ClassBase
            

class THierarchy(Type):

    def __init__( self ):
        Type.__init__(self)
        self.registry = {}  # id -> TClass
        self.cls2id = {}  # cls -> id

    def register( self, id, fields=None, cls=None, base=None ):
        assert isinstance(id, basestring), repr(id)
        assert fields is None or is_list_inst(fields, Field), repr(fields)
        assert base is None or isinstance(base, TClass), repr(base)
        assert id not in self.registry, 'Class id is already registered: %r' % id
        tclass = TClass(self, id, base, fields or [], cls)
        self.registry[id] = tclass
        if cls:
            self.cls2id[tclass.get_class()] = id
        return tclass

    def validate( self, path, obj ):
        self.resolve_obj(obj)._validate(path, obj)

    def resolve( self, id ):
        assert isinstance(id, basestring), repr(id)
        assert id in self.registry, 'Unknown class id: %r. Known are: %r' % (id, sorted(self.registry.keys()))
        return self.registry[id]

    def resolve_obj( self, obj ):
        id = self.cls2id.get(obj.__class__)
        if id is None:
            assert hasattr(obj, '_class_id'), repr(obj)  # not a TClass instance
            id = obj._class_id
        return self.resolve(id)
