from . types import (
    tString,
    tInt,
    Field,
    TList,
    )
from . interface import tHandle, tObjHandle


tFieldHandle = tHandle.register('field')

tStringFieldHandle = tHandle.register('string_field', base=tFieldHandle, fields=[Field('value', tString)])
StringFieldHandle = tStringFieldHandle.instantiate

tIntFieldHandle = tHandle.register('int_field', base=tFieldHandle, fields=[Field('value', tInt)])
IntFieldHandle = tIntFieldHandle.instantiate

tFormHandle = tHandle.register('form', base=tObjHandle, fields=[Field('fields', TList(tHandle))])
FormHandle = tFormHandle.instantiate
