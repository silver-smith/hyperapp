from hyperapp.common.htypes import tInt, Field, TRecord
from . import htypes


print('code module 1(%s):' % __name__)
print('test_module_1.record_1 =', htypes.test_module_1.record_1)

assert isinstance(htypes.test_module_1.record_1, TRecord)
assert Field('int_field', tInt) in htypes.test_module_1.record_1.fields

print('code module 1: done.')
