from collections import namedtuple, OrderedDict

from ..util import is_ordered_dict_inst
from .htypes import Type


def odict_all_match(x_fields, y_fields):
    return all(
        x_name == y_name and x_type.match(y_type)
        for (x_name, x_type), (y_name, y_type)
        in zip(x_fields.items(), y_fields.items()))


class TRecord(Type):

    def __init__(self, name, fields=None, base=None):
        assert name
        assert fields is None or is_ordered_dict_inst(fields, str, Type), repr(fields)
        assert base is None or isinstance(base, TRecord), repr(base)
        super().__init__(name)
        self.fields = fields or OrderedDict()
        if base:
            self.fields = OrderedDict(list(base.fields.items()) + list(self.fields.items()))
        self.base = base
        self._named_tuple = namedtuple(name, ['t'] + [name for name in self.fields])

    def __repr__(self):
        if self.name:
            return self.name
        else:
            return 'TRecord<%d: %s>' % (id(self), ', '.join("%r: %r" % (name, t) for name, t in self.fields.items()))

    def match(self, other):
        return (isinstance(other, TRecord)
                and odict_all_match(other.fields, self.fields))

    def __subclasscheck__(self, cls):
        ## print('__subclasscheck__', self, cls)
        if cls is self:
            return True
        if not isinstance(cls, TRecord):
            return False
        return issubclass(cls.base, self)

    def __call__(self, *args, **kw):
        return self.instantiate(*args, **kw)

    def __instancecheck__(self, rec):
        ## print '__instancecheck__', self, rec
        return issubclass(getattr(rec, 't', None), self)

    def instantiate(self, *args, **kw):
        return self._named_tuple(self, *args, **kw)
