print('code module import from code module main (%s):' % __name__)

from .import_from_code_module_sub import value

print('sub value =', value)

main_value = f'main:{value}'
