print('code module 2(%s):' % __name__)

from . import htypes
from .code_module_1 import module_1_var
from . import code_module_1

print('type_module_2.some_bool_list_opt =', htypes.type_module_2.some_bool_list_opt)
print('code_module_1 =', code_module_1)
print('module_1_var =', module_1_var)

print('code module 2: done.')
