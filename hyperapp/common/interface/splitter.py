from .types import Field
from .interface import tHandle, tViewHandle


tSplitterHandle = tHandle.register('two_side_selector', base=tViewHandle, fields=[
    Field('x', tHandle),
    Field('y', tHandle),
    ])

SplitterHandle = tSplitterHandle.instantiate
