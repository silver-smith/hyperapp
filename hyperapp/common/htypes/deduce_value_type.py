from .htypes import TRecord
from .hierarchy import TClass


def deduce_value_type(value):
    t = getattr(value, 't', None)
    if isinstance(t, TRecord):
        if isinstance(t, TClass):
            return t.hierarchy
        return t
    assert False, 'Add type parameter for values of types others than TRecord or THierarchy: {!r} ({!r})'.format(value, t)
