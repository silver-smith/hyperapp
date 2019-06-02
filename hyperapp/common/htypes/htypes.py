import datetime

from ..util import is_list_inst


class TypeError(Exception): pass


def join_path(*args):
    return '.'.join([_f for _f in args if _f])

def list_all_match(x_list, y_list):
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
