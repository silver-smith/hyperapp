import logging

from ..util import is_list_inst
from .htypes import join_path, Type, tString, Field, Record, TRecord, TList

log = logging.getLogger(__name__)


class TClassRecord(Record):

    def __init__(self, trec, tclass):
        assert isinstance(tclass, TClass), repr(tclass)
        Record.__init__(self, trec)
        self._class = tclass

    def __repr__(self):
        if self._class.hierarchy.full_name:
            name = '.'.join(self._class.hierarchy.full_name + [self._class.id])
        else:
            name = '.'.join('ClassRecord', self._class.hierarchy.hierarchy_id, self._class.id)
        return '%s<%s>' % (name, ', '.join(
            '%s=%r' % (field.name, getattr(self, field.name)) for field in self._type.fields))

    # public
    @property
    def _class_id(self):
        return self._class.id


class TClass(Type):

    def __init__(self, hierarchy, id, trec, base=None):
        assert isinstance(hierarchy, THierarchy), repr(hierarchy)
        assert isinstance(trec, TRecord), repr(trec)
        self.hierarchy = hierarchy
        self.id = id
        self.trec = trec
        self.base = base

    def __repr__(self):
        return '%s(%s.%s: %s)' % (self.__class__.__name__, self.hierarchy.hierarchy_id, self.id, ', '.join(map(repr, self.get_fields())))

    def __eq__(self, other):
        assert isinstance(other, TClass), repr(other)
        return other.hierarchy is self.hierarchy and other.id == self.id and other.trec == self.trec

    @property
    def full_name(self):
        return self.trec.full_name

    def __call__(self, *args, **kw):
        return self.instantiate(*args, **kw)

    def instantiate(self, *args, **kw):
        rec = TClassRecord(self.trec, self)
        self.trec.instantiate_impl(rec, *args, **kw)
        return rec

    def get_trecord(self):
        return self.trec

    def get_fields(self):
        return self.trec.fields

    def get_field(self, name):
        return self.trec.get_field(name)

    def __instancecheck__(self, rec):
        if not self.hierarchy.is_tclassrecord(rec):
            return False
        return issubclass(rec._class, self)

    def __subclasscheck__(self, tclass):
        if tclass is self:
            return True
        if not isinstance(tclass, TClass):
            return False
        if self.hierarchy is not tclass.hierarchy:
            return False
        if tclass.base and issubclass(tclass.base, self):
            return True
        return issubclass(tclass.get_trecord(), self.trec)
            

class THierarchy(Type):

    def __init__(self, hierarchy_id, full_name=None):
        super().__init__(full_name)
        self.hierarchy_id = hierarchy_id
        self.registry = {}  # id -> TClass

    def __repr__(self):
        return 'THierarchy(%s)' % self.hierarchy_id

    def __eq__(self, other):
        return other is self  # there must be only one (with same hierarchy_id)

    def matches(self, other):
        return (isinstance(other, THierarchy) and
                other.hierarchy_id == self.hierarchy_id and
                sorted(other.registry.values(), key=lambda cls: cls.id) ==
                sorted(self.registry.values(), key=lambda cls: cls.id))

    def register(self, id, trec=None, fields=None, base=None, full_name=None):
        assert isinstance(id, str), repr(id)
        assert id not in self.registry, 'Class id is already registered: %r' % id
        if trec is not None:
            assert fields is None and (base is None or base.fields == [])
            assert isinstance(trec, TRecord), repr(trec)
        else:
            assert fields is None or is_list_inst(fields, Field), repr(fields)
            assert base is None or isinstance(base, TClass), repr(base)
            if base:
                base_rec = base.get_trecord()
            else:
                base_rec = None
            trec = TRecord(fields, base_rec, full_name=full_name)
        tclass = self.make_tclass(id, trec, base)
        self.registry[id] = tclass
        #print('registered %s %s' % (self.hierarchy_id, id))
        return tclass

    def make_tclass(self, id, trec, base):
        return TClass(self, id, trec, base)

    def is_tclassrecord(self, rec):
        return isinstance(rec, TClassRecord)

    def __instancecheck__(self, rec):
        if not self.is_tclassrecord(rec):
            return False
        return rec._class.hierarchy is self

    def instance_hash(self, rec):
        return hash((rec._class_id, hash(rec)))  # class_id + fields

    def resolve(self, class_id):
        assert isinstance(class_id, str), repr(class_idid)
        assert class_id in self.registry, ('Unknown hierarchy %r class id: %r. Known are: %r, hierarchy id = %r'
            % (self.hierarchy_id, class_id, sorted(self.registry.keys()), id(self)))
        assert class_id in self.registry, 'Unknown hierarchy %r class id: %r. Known are: %r' % (self.hierarchy_id, class_id, sorted(self.registry.keys()))
        return self.registry[class_id]

    def get_object_class(self, rec):
        assert isinstance(rec, self), repr(rec)
        return rec._class

    def is_my_class(self, tclass):
        if not isinstance(tclass, TClass):
            return False
        return tclass.hierarchy is self


class TExceptionClassRecord(RuntimeError):

    def __init__(self, trec, tclass):
        assert isinstance(trec, TRecord), repr(trec)
        assert isinstance(tclass, TExceptionClass), repr(tclass)
        self._type = trec
        self._class = tclass

    def __str__(self):
        return '<%s.%s: %s>' % (self._class.hierarchy.hierarchy_id, self._class.id, ', '.join(
            '%s=%s' % (field.name, getattr(self, field.name)) for field in self._type.fields))

    def __repr__(self):
        return 'TExceptionClassRecord%s' % self

    # public
    @property
    def _class_id(self):
        return self._class.id


class TExceptionClass(TClass):

    def is_tclassrecord(self, rec):
        return isinstance(rec, TExceptionClassRecord)

    def instantiate(self, *args, **kw):
        rec = TExceptionClassRecord(self.trec, self)
        self.trec.instantiate_impl(rec, *args, **kw)
        return rec


class TExceptionHierarchy(THierarchy):

    def make_tclass(self, id, trec, base):
        return TExceptionClass(self, id, trec, base)

    def is_tclassrecord(self, rec):
        return isinstance(rec, TExceptionClassRecord)
