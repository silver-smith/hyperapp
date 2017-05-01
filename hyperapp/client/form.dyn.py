from ..common.interface.form import string_field_handle, int_field_handle, form_handle


def stringFieldHandle(value=None):
    return string_field_handle('string', value or '')

def intFieldHandle(value):
    return int_field_handle('int', value)

def formHandle(object, fields, current_field=0):
    return form_handle('form', object, fields, current_field)
