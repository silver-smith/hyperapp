import logging

from ..util import is_ordered_dict_inst
from .htypes import join_path, Type, tString, TList
from .record import odict_all_match, TRecord

log = logging.getLogger(__name__)


class TClass(TRecord):

    def __init__(self, hierarchy, id, fields=None, base=None):
        assert isinstance(hierarchy, THierarchy), repr(hierarchy)
        super().__init__(id, fields, base)
        self.hierarchy = hierarchy

    @property
    def id(self):
        return self._name

    def __repr__(self):
        return "%s('%s.%s': [%s])" % (self.__class__.__name__, self.hierarchy.hierarchy_id, self.id, ', '.join(map(repr, self.fields.values())))

    def match(self, other):
        assert isinstance(other, TClass), repr(other)
        return (other.hierarchy.hierarchy_id == self.hierarchy.hierarchy_id
                and other.id == self.id
                and odict_all_match(other.fields, self.fields))


class THierarchy(Type):

    def __init__(self, hierarchy_id, name=None):
        super().__init__(name or hierarchy_id)
        self.hierarchy_id = hierarchy_id
        self.registry = {}  # id -> TClass

    def __repr__(self):
        return 'THierarchy(%r)' % self.hierarchy_id

    def match(self, other):
        return (isinstance(other, THierarchy) and
                other.hierarchy_id == self.hierarchy_id and
                sorted(other.registry.values(), key=lambda cls: cls.id) ==
                sorted(self.registry.values(), key=lambda cls: cls.id))

    def register(self, id, fields=None, base=None):
        assert isinstance(id, str), repr(id)
        assert id not in self.registry, 'Class id is already registered: %r' % id
        assert fields is None or is_ordered_dict_inst(fields, str, Type), repr(fields)
        assert base is None or isinstance(base, TClass), repr(base)
        tclass = self.make_tclass(id, fields, base)
        self.registry[id] = tclass
        #print('registered %s %s' % (self.hierarchy_id, id))
        return tclass

    def make_tclass(self, id, fields, base):
        return TClass(self, id, fields, base)

    def is_tclassrecord(self, rec):
        return isinstance(getattr(rec, 't', None), TRecord)

    def __instancecheck__(self, rec):
        if not self.is_tclassrecord(rec):
            return False
        return rec.t.hierarchy is self

    def resolve(self, class_id):
        assert isinstance(class_id, str), repr(class_id)
        assert class_id in self.registry, ('Unknown hierarchy %r class id: %r. Known are: %r, hierarchy id = %r'
            % (self.hierarchy_id, class_id, sorted(self.registry.keys()), id(self)))
        assert class_id in self.registry, 'Unknown hierarchy %r class id: %r. Known are: %r' % (self.hierarchy_id, class_id, sorted(self.registry.keys()))
        return self.registry[class_id]

    def get_object_class(self, rec):
        assert isinstance(rec, self), repr(rec)
        return rec.t

    def is_my_class(self, tclass):
        if not isinstance(tclass, TClass):
            return False
        return tclass.hierarchy is self
