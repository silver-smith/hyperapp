from .iface_types import tString, Field
from .interface import tObject, tBaseObject


tTextObject = tObject.register('text', base=tBaseObject, fields=[Field('text', tString)])
TextObject = tTextObject.instantiate
