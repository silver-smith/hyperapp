from hyperapp.common.htypes import tInt, Field, TRecord
from . import htypes


print('code module 1(%s):' % __name__)
print('type_module_1.record_1 =', htypes.type_module_1.record_1)

assert isinstance(htypes.type_module_1.record_1, TRecord)
assert Field('int_field', tInt) in htypes.type_module_1.record_1.fields

print('code module 1: done.')
