from hyperapp.common.htypes import tInt, TRecord
from . import htypes


print('code module 1(%s):' % __name__)
print('type_module_1.record_1 =', htypes.type_module_1.record_1)

assert isinstance(htypes.type_module_1.record_1, TRecord)
assert htypes.type_module_1.record_1.fields['int_field'] is tInt

module_1_var = 'module 1 var value'

print('code module 1: done.')
