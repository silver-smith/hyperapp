from .htypes import TRecord


def deduce_value_type(value):
    t = getattr(value, 't', None)
    if isinstance(t, TRecord):
        return t
    assert False, 'Add type parameter for values of types others than TRecord or THierarchy: {!r} ({!r})'.format(value, t)
