from .types import (
    tString,
    tInt,
    Field,
    TRecord,
    TList,
    )
from .hierarchy import THierarchy
from .interface import tHandle, tObjHandle


tFieldHandle = THierarchy('form_field')
tBaseFieldHandle = tFieldHandle.register('field', fields=[Field('field_view_id', tString)])

tStringFieldHandle = tFieldHandle.register('string_field', base=tBaseFieldHandle, fields=[Field('value', tString)])
tIntFieldHandle = tFieldHandle.register('int_field', base=tBaseFieldHandle, fields=[Field('value', tInt)])

tFormField = TRecord([
    Field('name', tString),
    Field('field_handle', tFieldHandle),
    ])
FormField = tFormField.instantiate


tFormHandle = tHandle.register('form', base=tObjHandle, fields=[
    Field('fields', TList(tFormField)),
    Field('current_field', tInt, default=0),
    ])
FormHandle = tFormHandle.instantiate
