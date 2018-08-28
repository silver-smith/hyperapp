from .htypes import Record
from .hierarchy import TClassRecord, TExceptionClassRecord


def deduce_value_type(value):
    if isinstance(value, (TClassRecord, TExceptionClassRecord)):
        return value._class.hierarchy
    if isinstance(value, Record):
        return value._type
    assert False, 'Add type parameter for values of types others than TRecord or THierarchy'
