import datetime

from ..util import is_iterable_inst


BUILTIN_MODULE_NAME = 'builtin'


class TypeError(Exception): pass


def join_path(*args):
    return '.'.join([_f for _f in args if _f])


class Type:

    def __init__(self, module_name, name):
        assert module_name is None or type(module_name) is str, repr(module_name)
        assert name is None or type(name) is str, repr(name)
        self._module_name = module_name
        self._name = name

    @property
    def module_name(self):
        return self._module_name

    @property
    def name(self):
        return self._name

    @property
    def full_name(self):
        return f'{self.module_name}.{self.name}'

    def __instancecheck__(self, value):
        raise NotImplementedError(self.__class__)


class TPrimitive(Type):

    # type - defined in children.

    def __init__(self, module_name, name):
        super().__init__(module_name, name)

    def __repr__(self):
        return '%s' % self.get_type().__name__

    def __hash__(self):
        return hash(self._name)

    def __eq__(self, rhs):
        return rhs is self or isinstance(rhs, TPrimitive) and rhs._name == self._name

    def __instancecheck__(self, value):
        return isinstance(value, self.get_type())

    def get_type(self):
        return self.type


class TNone(TPrimitive):
    type = type(None)

class TString(TPrimitive):
    type = str

class TBinary(TPrimitive):
    type = bytes

class TInt(TPrimitive):
    type = int

class TBool(TPrimitive):
    type = bool

class TDateTime(TPrimitive):
    type = datetime.datetime


tNone = TNone(BUILTIN_MODULE_NAME, 'none')
tString = TString(BUILTIN_MODULE_NAME, 'string')
tBinary = TBinary(BUILTIN_MODULE_NAME, 'binary')
tInt = TInt(BUILTIN_MODULE_NAME, 'int')
tBool = TBool(BUILTIN_MODULE_NAME, 'bool')
tDateTime = TDateTime(BUILTIN_MODULE_NAME, 'datetime')


class TOptional(Type):

    def __init__(self, base_t, module_name=None, name=None):
        assert isinstance(base_t, Type), repr(base_t)
        super().__init__(module_name, name)
        self.base_t = base_t

    def __repr__(self):
        return '%r opt' % self.base_t

    def __hash__(self):
        return hash(('optional', self.base_t))

    def __eq__(self, rhs):
        return rhs is self or isinstance(rhs, TOptional) and rhs.base_t == self.base_t

    def __instancecheck__(self, value):
        return value is None or isinstance(value, self.base_t)


class TList(Type):

    def __init__(self, element_t, module_name=None, name=None):
        assert isinstance(element_t, Type), repr(element_t)
        super().__init__(module_name, name)
        self.element_t = element_t

    def __repr__(self):
        return '%r list' % self.element_t

    def __hash__(self):
        return hash(('list', self.element_t))

    def __eq__(self, rhs):
        return rhs is self or isinstance(rhs, TList) and rhs.element_t == self.element_t

    def __instancecheck__(self, value):
        return is_iterable_inst(value, self.element_t)
