from ..util import is_list_inst
from .htypes import join_path, Type, tString, Field, Record, TRecord, TList


class TClassRecord(Record):

    def __init__( self, trec, tclass ):
        Record.__init__(self, trec)
        self._class = tclass


class TClass(TRecord):

    def __init__( self, hierarchy, id, trec ):
        TRecord.__init__(self)
        self.hierarchy = hierarchy
        self.id = id
        self.trec = trec

    def __repr__( self ):
        return 'TClass(%s: %s)' % (self.id, ', '.join(map(repr, self.get_fields())))

    def __eq__( self, other ):
        assert isinstance(other, TClass), repr(other)
        return other.hierarchy is self.hierarchy and other.id == self.id and other.trec == self.trec

    def get_trecord( self ):
        return self.trec

    def get_fields( self ):
        return self.trec.get_fields()

    def get_field( self, name ):
        return self.trec.get_field(name)

    def __instancecheck__( self, obj ):
        if not isinstance(obj, TClassRecord):
            return False
        return issubclass(obj._class, self)

    def instantiate( self, *args, **kw ):
        rec = TClassRecord(self.trec, self)
        self.trec.instantiate_impl(rec, *args, **kw)
        return rec

    def __subclasscheck__( self, tclass ):
        if not isinstance(tclass, TClass):
            return False
        if tclass is self:
            return True
        if self.hierarchy is not tclass.hierarchy:
            return False
        return issubclass(tclass.get_trecord(), self.trec)
            

class THierarchy(Type):

    def __init__( self, hierarchy_id ):
        Type.__init__(self)
        self.hierarchy_id = hierarchy_id
        self.registry = {}  # id -> TClass

    def __repr__( self ):
        return 'THierarchy(%s)' % self.hierarchy_id

    def __eq__( self, other ):
        return other is self  # there must be only one (with same hierarchy_id)

    def matches( self, other ):
        return (isinstance(other, THierarchy) and
                other.hierarchy_id == self.hierarchy_id and
                sorted(other.registry.values(), key=lambda cls: cls.id) ==
                sorted(self.registry.values(), key=lambda cls: cls.id))

    def register( self, id, trec=None, fields=None, base=None ):
        assert isinstance(id, str), repr(id)
        assert id not in self.registry, 'Class id is already registered: %r' % id
        if trec is not None:
            assert fields is None and base is None
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

    def __instancecheck__( self, rec ):
        if not isinstance(rec, TClassRecord):
            return False
        return rec._class.hierarchy is self

    def resolve( self, id ):
        assert isinstance(id, str), repr(id)
        assert id in self.registry, 'Unknown class id: %r. Known are: %r' % (id, sorted(self.registry.keys()))
        return self.registry[id]

    def resolve_obj( self, rec ):
        assert isinstance(rec, TClassRecord), repr(rec)
        return rec._class
