from ..htypes import (
    tString,
    Field,
    tObject,
    tBaseObject,
    )


tTextObject = tObject.register('text', base=tBaseObject, fields=[Field('text', tString)])
