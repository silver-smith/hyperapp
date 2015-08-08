from . types import (
    tString,
    tInt,
    Field,
    TRecord,
    TList,
    )
from . interface import tHandle, tObjHandle


tFieldHandle = tHandle.register('field')

tStringFieldHandle = tHandle.register('string_field', base=tFieldHandle, fields=[Field('value', tString)])
StringFieldHandle = tStringFieldHandle.instantiate

tIntFieldHandle = tHandle.register('int_field', base=tFieldHandle, fields=[Field('value', tInt)])
IntFieldHandle = tIntFieldHandle.instantiate

tFormField = TRecord([
    Field('name', tString),
    Field('handle', tHandle),
    ])
FormField = tFormField.instantiate


tFormHandle = tHandle.register('form', base=tObjHandle, fields=[
    Field('fields', TList(tFormField)),
    Field('current_field', tInt),
    ])

class FormHandle(tFormHandle.make_class()):

    def __init__( self, view_id, object, fields, current_field=0 ):
        super(FormHandle, self).__init__(view_id, object, fields, current_field)
