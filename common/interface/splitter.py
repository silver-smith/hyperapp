from . types import Field
from . interface import tHandle, tSimpleHandle


tSplitterHandle = tHandle.register('two_side_selector', base=tSimpleHandle, fields=[
    Field('x', tHandle),
    Field('y', tHandle),
    ])

SplitterHandle = tSplitterHandle.instantiate
