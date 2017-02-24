from .htypes import (
    tBool,
    tString,
    TOptional,
    TList,
    Field,
    TRecord,
    )
from .hierarchy import THierarchy


tResource = THierarchy('resource')

tCommandResource = tResource.register('command', fields=[
    Field('is_default', tBool),
    Field('text', tString),
    Field('description', TOptional(tString)),
    Field('shortcuts', TList(tString), default=[]),
    ])

tColumnResource = tResource.register('column', fields=[
    Field('visible', tBool),
    Field('text', TOptional(tString)),
    Field('description', TOptional(tString)),
    ])

tResourceId = TList(tString)

tResourceRec = TRecord([
    Field('id', tResourceId),
    Field('resource', tResource),
    ])

tResourceList = TList(tResourceRec)
