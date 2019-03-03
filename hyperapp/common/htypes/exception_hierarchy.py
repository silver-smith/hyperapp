from keyword import iskeyword as _iskeyword
import sys as _sys

from .hierarchy import TClass, THierarchy


# We want exception hierarchy instances to inherit from Exception.
# Use same code as namedtuple from collections for this.


_class_template = """\
from builtins import property as _property
from operator import itemgetter as _itemgetter
from collections import OrderedDict

class {typename}(Exception):
    '{typename}({arg_list})'

    __slots__ = {field_names!r}

    def __init__(self, {arg_list}):
        super().__init__("{typename}({repr_fmt})" % ({arg_list}))
        {init_fields}

    def __iter__(self):
        return iter(({attr_list}))

    def __getitem__(self, index):
        return ({attr_list})[index]

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new {typename} object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != {num_fields:d}:
            raise TypeError('Expected {num_fields:d} arguments, got %d' % len(result))
        return result

    def _replace(_self, **kwds):
        'Return a new {typename} object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, {field_names!r}, _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % list(kwds))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + '({repr_fmt})' % ({attr_list})

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values.'
        return OrderedDict(zip(self._fields, self))

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)
"""

_repr_template = '{name}=%r'
_init_field_template = '''
        self.{name} = {name}'''


def _make_exception_class(typename, field_names):
    # Validate the field names.  At the user's option, either generate an error
    # message or automatically replace the field name with a valid name.
    if isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    field_names = list(map(str, field_names))
    typename = str(typename)
    for name in [typename] + field_names:
        if type(name) != str:
            raise TypeError('Type names and field names must be strings')
        if not name.isidentifier():
            raise ValueError('Type names and field names must be valid '
                             'identifiers: %r' % name)
        if _iskeyword(name):
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
    class_definition = _class_template.format(
        typename = typename,
        field_names = tuple(field_names),
        num_fields = len(field_names),
        arg_list = repr(tuple(field_names)).replace("'", "")[1:-1],
        attr_list = ', '.join('self.{}'.format(name) for name in field_names),
        repr_fmt = ', '.join(_repr_template.format(name=name)
                             for name in field_names),
        init_fields= ''.join(_init_field_template.format(name=name) for name in field_names).lstrip(),
    )
    print(class_definition)

    # Execute the template string in a temporary namespace and support
    # tracing utilities by setting a value for frame.f_globals['__name__']
    namespace = dict(__name__='exception_tuple_%s' % typename)
    exec(class_definition, namespace)
    result = namespace[typename]
    result._source = class_definition

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in environments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython).
    try:
        result.__module__ = _sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return result


class TExceptionClass(TClass):

    def __init__(self, hierarchy, id, fields=None, base=None):
        super().__init__(hierarchy, id, fields, base)
        self._exception_class = _make_exception_class(id, ['t'] + [field.name for field in self.fields])

    def instantiate(self, *args, **kw):
        return self._exception_class(self, *args, **kw)


class TExceptionHierarchy(THierarchy):

    def make_tclass(self, id, trec, base):
        return TExceptionClass(self, id, trec, base)
