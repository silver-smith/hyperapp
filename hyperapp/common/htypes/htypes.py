from collections import namedtuple, OrderedDict
import datetime

from ..util import is_list_inst, is_ordered_dict_inst


class TypeError(Exception): pass


def join_path(*args):
    return '.'.join([_f for _f in args if _f])

def list_all_match(x_list, y_list):
    return all(x.match(y) for x, y in zip(x_list, y_list))

def odict_all_match(x_fields, y_fields):
    return all(
        x_name == y_name and x_type.match(y_type)
        for (x_name, x_type), (y_name, y_type)
        in zip(x_fields.items(), y_fields.items()))


class Type(object):

    def __init__(self, name):
        assert name is None or type(name) is str, repr(name)
        self._name = name

    @property
    def name(self):
        return self._name

    def __instancecheck__(self, value):
        raise NotImplementedError(self.__class__)


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

tServerRoutes = TRecord('server_routes', OrderedDict([
    ('public_key_der', tBinary),
    ('routes', TList(tRoute)),
    ]))

tIfaceId = TString(name='iface_id')

tPath = TList(tString, name='path')

tUrl = TRecord('url', OrderedDict([
    ('iface', tIfaceId),
    ('public_key_der', tBinary),
    ('path', tPath),
    ]))

tUrlWithRoutes = TRecord('url_with_routes', base=tUrl, fields=OrderedDict([
    ('routes', TList(tRoute)),
    ]))
