from ..util import is_list_inst
from .htypes import join_path, Type, tString, Field, Record, TRecord, TList


class TClassRecord(Record):

    def __init__( self, trec, tclass ):
        Record.__init__(self, trec)
        self._class = tclass


class TClass(TRecord):

    type_id = 'hierarchy_class'

    @classmethod
    def from_data( cls, registry, hierarchy, rec ):
        fields = [Field.from_data(registry, field) for field in rec.fields]
        return cls(hierarchy, rec.id, TRecord(fields))

    def __init__( self, hierarchy, id, trec ):
        TRecord.__init__(self)
        self.hierarchy = hierarchy
        self.id = id
        self.trec = trec

    def __repr__( self ):
        return 'TClass(%s: %s)' % (self.id, ', '.join(map(repr, self.get_fields())))

    def __eq__( self, other ):
        assert isinstance(other, TClass), repr(other)
        return other.id == self.id and other.trec == self.trec

    @classmethod
    def register_meta( cls ):
        lbtypes.tHierarchyClassMeta = TRecord(base=lbtypes.tRecordMeta, fields=[
            Field('id', tString),
            ])

    def to_data( self ):
        return lbtypes.tHierarchyClassMeta(self.type_id, [field.to_data() for field in self.get_fields()], self.id)

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

    type_id = 'hierarchy'

    @classmethod
    def from_data( cls, registry, rec ):
        hierarchy = cls(rec.hierarchy_id)
        for class_rec in rec.classes:
            tclass = TClass.from_data(registry, hierarchy, class_rec)
            hierarchy.register(tclass.id, tclass.trec)
        return hierarchy

    def __init__( self, hierarchy_id ):
        Type.__init__(self)
        self.hierarchy_id = hierarchy_id
        self.registry = {}  # id -> TClass

    def __repr__( self ):
        return 'THierarchy(%s)' % self.hierarchy_id

    def __eq__( self, other ):
        return (isinstance(other, THierarchy) and
                other.hierarchy_id == self.hierarchy_id and
                sorted(other.registry.values(), key=lambda cls: cls.id) ==
                sorted(self.registry.values(), key=lambda cls: cls.id))

    @classmethod
    def register_meta( cls ):
        TClass.register_meta()
        lbtypes.tHierarchyMeta = lbtypes.tMetaType.register(cls.type_id, base=lbtypes.tRootMetaType, fields=[
            Field('hierarchy_id', tString),
            Field('classes', TList(lbtypes.tHierarchyClassMeta)),
            ])

    @classmethod
    def register_type( cls, type_registry ):
        type_registry.register(cls.type_id, cls.from_data)

    def to_data( self ):
        return lbtypes.tHierarchyMeta(
            self.type_id, self.hierarchy_id,
            [cls.to_data() for cls in self.registry.values()])

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
