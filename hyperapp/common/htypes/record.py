from collections import OrderedDict
from keyword import iskeyword
import sys

from ..util import is_ordered_dict_inst
from .htypes import Type


def odict_all_match(x_fields, y_fields):
    return all(
        x_name == y_name and x_type.match(y_type)
        for (x_name, x_type), (y_name, y_type)
        in zip(x_fields.items(), y_fields.items()))

# We want record instances have '_t' member, excluded from _asdict() results.
# namedtuple from collections forbits members started from underscores.
# This is copied and adjusted namedtuple implementation from collections module.

_class_template = """\
from builtins import property as _property, tuple as _tuple
from operator import itemgetter as _itemgetter
from collections import OrderedDict

class {typename}(tuple):
    '{typename}({arg_list})'

    __slots__ = ()

    _fields = {field_names!r}

    def __new__(_cls, {arg_list_with_comma} _t):
        'Create new instance of {typename}({arg_list})'
        return _tuple.__new__(_cls, ({arg_list_with_comma} _t,))

    @classmethod
    def _make(cls, _t, iterable, new=tuple.__new__, len=len):
        'Make a new {typename} object from a sequence or iterable'
        result = new(cls, (*iterable, _t))
        if len(result) != {num_fields:d} + 1:
            raise TypeError('Expected {num_fields:d} arguments, got %d' % len(result))
        return result

    def _replace(_self, **kwds):
        'Return a new {typename} object replacing specified fields with new values'
        result = _self._make(_self._t, map(kwds.pop, {field_names!r}, _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % list(kwds))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + '({repr_fmt})' % self[:-1]

    def __iter__(self):
        return iter(({attr_list}))

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values.'
        return OrderedDict(zip(self._fields, self[:-1]))

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(*(*self, self_t))

{field_defs}
"""

_repr_template = '{name}=%r'

_field_template = '''\
    {name} = _property(_itemgetter({index:d}), doc='Alias for field number {index:d}')
'''

def _namedtuple(typename, field_names, verbose=False, rename=False):

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
    class_definition = _class_template.format(
        typename = typename,
        field_names = tuple(field_names),
        num_fields = len(field_names),
        arg_list = arg_list,
        arg_list_with_comma = arg_list + ',' if arg_list else '',
        attr_list = ', '.join('self.{}'.format(name) for name in field_names),
        repr_fmt = ', '.join(_repr_template.format(name=name)
                             for name in field_names),
        field_defs = '\n'.join(_field_template.format(index=index, name=name)
                               for index, name in enumerate(field_names + ['_t']))
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


class TRecord(Type):

    def __init__(self, name, fields=None, base=None, verbose=False):
        assert name
        assert fields is None or is_ordered_dict_inst(fields, str, Type), repr(fields)
        assert base is None or isinstance(base, TRecord), repr(base)
        super().__init__(name)
        self.fields = fields or OrderedDict()
        if base:
            self.fields = OrderedDict(list(base.fields.items()) + list(self.fields.items()))
        self.base = base
        self._named_tuple = _namedtuple(name, [name for name in self.fields], verbose)

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
        return issubclass(getattr(rec, '_t', None), self)

    def instantiate(self, *args, **kw):
        return self._named_tuple(*args, _t=self, **kw)
