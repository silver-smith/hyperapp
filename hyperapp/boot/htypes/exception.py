import codecs
import sys
from keyword import iskeyword

from ..util import is_dict_inst
from .htypes import Type, tString, tBinary


CHECK_FIELD_TYPES = True


class HException(Exception):
    pass


# This is copied and adjusted namedtuple implementation from collections module.

# We want record instances have '_t' member, excluded from _asdict() results.
# namedtuple from collections forbids members started from underscores.

_class_template = """\
from builtins import property as _property
from operator import itemgetter as _itemgetter

from hyperapp.boot.htypes.exception import HException


class {typename}(HException):
    '{typename}({arg_list})'

    __slots__ = ()

    _fields = {field_names!r}

    def __init__(self, {arg_list_with_comma} _t):
{fields_init}

    def __str__(self):
        return {str_fmt}

    def __repr__(self):
        return {repr_fmt}

    def __iter__(self):
        return iter(({attr_list_with_comma}))

    def __eq__(self, rhs):
        return self._t == rhs._t and tuple(self) == tuple(rhs)

    def __hash__(self):
        return hash((self._t, {attr_list}))

    def __getitem__(self, idx):
        return ({attr_list})[idx]

    def _asdict(self):
        'Return a new dict which maps field names to their values.'
        return dict(zip(self._fields, self))
"""

_repr_template = '{name}=%r'

_field_init_template = '''\
      self.{name} = {name}'''


def _namedtuple(typename, field_names, verbose=False, rename=False, str_fmt=None, repr_fmt=None):

    # Validate the field names.  At the user's option, either generate an error
    # message or automatically replace the field name with a valid name.
    if isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    field_names = list(map(str, field_names))
    typename = str(typename)
    if rename:
        seen = set()
        for index, name in enumerate(field_names):
            if (not name.isidentifier()
                or iskeyword(name)
                or name.startswith('_')
                or name in seen):
                field_names[index] = '_%d' % index
            seen.add(name)
    for name in [typename] + field_names:
        if type(name) != str:
            raise TypeError('Type names and field names must be strings')
        if not name.isidentifier():
            raise ValueError('Type names and field names must be valid '
                             'identifiers: %r' % name)
        if iskeyword(name):
            raise ValueError('Type names and field names cannot be a '
                             'keyword: %r' % name)
    seen = set()
    for name in field_names:
        if name.startswith('_') and not rename:
            raise ValueError('Field names cannot start with an underscore: '
                             '%r' % name)
        if name in seen:
            raise ValueError('Encountered duplicate field name: %r' % name)
        seen.add(name)

    # Fill-in the class template
    arg_list = ', '.join(field_names)
    attr_list = ', '.join(f'self.{name}' for name in field_names)
    if field_names:
        attr_list_with_comma = f'{attr_list},'
    else:
        attr_list_with_comma = ''
    class_definition = _class_template.format(
        typename=typename,
        field_names=tuple(field_names),
        num_fields=len(field_names),
        arg_list=arg_list,
        arg_list_with_comma=arg_list + ',' if arg_list else '',
        attr_list=attr_list,
        attr_list_with_comma=attr_list_with_comma,
        str_fmt=str_fmt,
        repr_fmt=repr_fmt,
        fields_init='\n'.join(_field_init_template.format(name=name)
                               for name in field_names + ['_t'])
    )

    # Execute the template string in a temporary namespace and support
    # tracing utilities by setting a value for frame.f_globals['__name__']
    namespace = dict(__name__='namedtuple_%s' % typename)
    exec(class_definition, namespace)
    result = namespace[typename]
    result._source = class_definition
    if verbose:
        print(result._source)

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in environments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython).
    try:
        result.__module__ = sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return result


class TException(Type):

    def __init__(self, module_name, name, fields=None, base=None, verbose=False):
        assert name
        assert fields is None or is_dict_inst(fields, str, Type), repr(fields)
        assert base is None or isinstance(base, TException), repr(base)
        super().__init__(module_name, name)
        self.fields = fields or {}
        if base:
            self.fields = {**base.fields, **self.fields}
        self.base = base
        self._named_tuple = _namedtuple(
            name, [name for name in self.fields], verbose, str_fmt=self._str_fmt(), repr_fmt=self._repr_fmt())
        self._eq_key = (self._name, *self.fields.items())

    def __str__(self):
        return f'TException({self.name!r})'

    def __repr__(self):
        fields = ', '.join("%s: %r" % (name, t) for name, t in self.fields.items())
        return f"{self.module_name}.{self.name}({fields or ('(no fields)')})"

    def _str_fmt(self):
        return self._repr_fmt()

    def _repr_fmt(self):
        fields_format = ', '.join(
            _repr_template.format(name=name)
            for name in self.fields
            )
        return f'self.__class__.__name__ + "({fields_format})" % tuple(self)'

    def __hash__(self):
        return hash(self._eq_key)

    def __eq__(self, rhs):
        return (rhs is self
                or (isinstance(rhs, TException) and rhs._eq_key == self._eq_key))

    def __subclasscheck__(self, cls):
        ## print('__subclasscheck__', self, cls)
        if cls is self:
            return True
        if not isinstance(cls, TException):
            return False
        return issubclass(cls.base, self)

    def __call__(self, *args, **kw):
        return self.instantiate(*args, **kw)

    def __instancecheck__(self, rec):
        ## print '__instancecheck__', self, rec
        return issubclass(getattr(rec, '_t', None), self)

    def instantiate(self, *args, **kw):
        if CHECK_FIELD_TYPES:
            self._check_field_types(*args, **kw)
        return self._named_tuple(*args, _t=self, **kw)

    def _check_field_types(self, *args, **kw):
        for (name, t), value in zip(self.fields.items(), args):
            assert isinstance(value, t), f"{name}: expected {t}, but got: {value!r}"
        for name, value in kw.items():
            t = self.fields[name]
            assert isinstance(value, t), f"{name}: expected {t}, but got: {value!r}"
