from ..util import is_list_inst
from .iface_types import join_path, Type, Field, TRecord


REC_CLASS_ID_ATTR = '_class_id'


class TClass(TRecord):

    def __init__( self, hierarchy, id, trec ):
        TRecord.__init__(self)
        self.hierarchy = hierarchy
        self.id = id
        self.trec = trec

    def get_trecord( self ):
        return self.trec

    def get_fields( self ):
        assert False  # must not be called

    def validate( self, path, obj ):
        return self.trec.validate(path, obj)

    def instantiate( self, *args, **kw ):
        rec = self.trec.instantiate(*args, **kw)
        setattr(rec, REC_CLASS_ID_ATTR, self.id)
        return rec

    def issubclass( self, trec ):
        return self is trec or self.trec.issubclass(trec)
            

class THierarchy(Type):

    def __init__( self, hierarchy_id ):
        Type.__init__(self)
        self.hierarchy_id = hierarchy_id
        self.registry = {}  # id -> TClass

    def register( self, id, trec=None, fields=None, base=None ):
        assert isinstance(id, basestring), repr(id)
        assert id not in self.registry, 'Class id is already registered: %r' % id
        if trec is not None:
            assert isinstance(trec, TRecord), repr(trec)
        else:
            assert fields is None or is_list_inst(fields, Field), repr(fields)
            assert base is None or isinstance(base, TClass), repr(base)
            if base:
                base_rec = base.get_trecord()
            else:
                base_rec = None
            trec = TRecord(fields, base_rec)
        tclass = TClass(self, id, trec)
        self.registry[id] = tclass
        return tclass

    def validate( self, path, obj ):
        self.resolve_obj(obj).validate(path, obj)

    def resolve( self, id ):
        assert isinstance(id, basestring), repr(id)
        assert id in self.registry, 'Unknown class id: %r. Known are: %r' % (id, sorted(self.registry.keys()))
        return self.registry[id]

    def resolve_obj( self, obj ):
        id = getattr(obj, REC_CLASS_ID_ATTR, None)
        assert id is not None, repr(obj)  # not a TClass instance
        return self.resolve(id)

    def isinstance( self, obj, trec ):
        return self.resolve_obj(obj).issubclass(trec)
