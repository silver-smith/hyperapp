from collections import namedtuple
import datetime

from ..util import is_list_inst


class TypeError(Exception): pass


def join_path(*args):
    return '.'.join([_f for _f in args if _f])

def all_match(x_list, y_list):
    return all(x.match(y) for x, y in zip(x_list, y_list))


class Type(object):

    def __init__(self, name):
        assert name is None or type(name) is str, repr(name)
        self._name = name

    @property
    def name(self):
        return self._name

    def __instancecheck__(self, value):
        raise NotImplementedError(self.__class__)

    def expect(self, path, value, name, expr):
        if not expr:
            self.failure(path, '%s is expected, but got: %r' % (name, value))

    def assert_(self, path, expr, desc):
        if not expr:
            self.failure(path, desc)

    def failure(self, path, desc):
        raise TypeError('%s: %s' % (path, desc))


class TPrimitive(Type):

    def __init__(self, name=None):
        super().__init__(name or self.type_name)

    def __repr__(self):
        return 'TPrimitive<%s>' % self.get_type().__name__

    def match(self, other):
        return isinstance(other, TPrimitive) and other.type_name == self.type_name

    def __instancecheck__(self, value):
        return isinstance(value, self.get_type())

    def get_type(self):
        return self.type


class TNone(TPrimitive):
    type_name = 'none'
    type = type(None)

class TString(TPrimitive):
    type_name = 'string'
    type = str

class TBinary(TPrimitive):
    type_name = 'binary'
    type = bytes

class TInt(TPrimitive):
    type_name = 'int'
    type = int

class TBool(TPrimitive):
    type_name = 'bool'
    type = bool

class TDateTime(TPrimitive):
    type_name = 'datetime'
    type = datetime.datetime


tNone = TNone()
tString = TString()
tBinary = TBinary()
tInt = TInt()
tBool = TBool()
tDateTime = TDateTime()


class TOptional(Type):

    def __init__(self, base_t, name=None):
        assert isinstance(base_t, Type), repr(base_t)
        super().__init__(name)
        self.base_t = base_t

    def __repr__(self):
        return 'TOptional<%r>' % self.base_t

    def match(self, other):
        return isinstance(other, TOptional) and other.base_t.match(self.base_t)

    def __instancecheck__(self, value):
        return value is None or isinstance(value, self.base_t)


class Field(object):

    @classmethod
    def from_data(cls, registry, rec):
        return cls(rec.name, registry.resolve(rec.type))

    def __init__(self, name, type):
        assert isinstance(name, str), repr(name)
        assert isinstance(type, Type), repr(type)
        self.name = name
        self.type = type

    def isinstance(self, value):
        if not self.type:
            return True  # todo: check why
        return isinstance(value, self.type)

    def __repr__(self):
        return '%r: %r' % (self.name, self.type)

    def match(self, other):
        assert isinstance(other, Field), repr(other)
        return other.name == self.name and other.type.match(self.type)


class TRecord(Type):

    def __init__(self, name, fields=None, base=None):
        assert name
        assert is_list_inst(fields or [], Field), repr(fields)
        assert base is None or isinstance(base, TRecord), repr(base)
        super().__init__(name)
        self.fields = fields or []
        if base:
            self.fields = base.fields + self.fields
        self.base = base
        self._named_tuple = namedtuple(name, ['t'] + [field.name for field in self.fields])

    def __repr__(self):
        if self.name:
            return self.name
        else:
            return 'TRecord<%d: %s>' % (id(self), ', '.join(map(repr, self.fields)))

    def match(self, other):
        return (isinstance(other, TRecord)
                and all_match(other.fields, self.fields))

    def __subclasscheck__(self, cls):
        ## print('__subclasscheck__', self, cls)
        if cls is self:
            return True
        if not isinstance(cls, TRecord):
            return False
        return issubclass(cls.base, self)

    def __call__(self, *args, **kw):
        return self.instantiate(*args, **kw)

    def get_field(self, name):
        for field in self.fields:
            if field.name == name:
                return field
        assert False, repr((name, self.fields))  # Unknown field

    def __instancecheck__(self, rec):
        ## print '__instancecheck__', self, rec
        return issubclass(getattr(rec, 't', None), self)

    def instantiate(self, *args, **kw):
        return self._named_tuple(self, *args, **kw)


class TList(Type):

    def __init__(self, element_t, name=None):
        assert isinstance(element_t, Type), repr(element_t)
        super().__init__(name)
        self.element_t = element_t

    def __repr__(self):
        return 'TList<%r>' % self.element_t

    def match(self, other):
        return isinstance(other, TList) and other.element_t.match(self.element_t)

    def __instancecheck__(self, value):
        return is_list_inst(value, self.element_t)


class TIndexedList(TList):
    pass


tRoute = TList(tString, name='route')

tServerRoutes = TRecord('server_routes', [
    Field('public_key_der', tBinary),
    Field('routes', TList(tRoute)),
    ])

tIfaceId = TString(name='iface_id')

tPath = TList(tString, name='path')

tUrl = TRecord('url', [
    Field('iface', tIfaceId),
    Field('public_key_der', tBinary),
    Field('path', tPath),
    ])

tUrlWithRoutes = TRecord('url_with_routes', base=tUrl, fields=[
    Field('routes', TList(tRoute)),
    ])
