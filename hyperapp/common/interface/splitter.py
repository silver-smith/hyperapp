from ..htypes import tString, Field, tHandle, tViewHandle


tSplitterHandle = tHandle.register('splitter', base=tViewHandle, fields=[
    Field('x', tHandle),
    Field('y', tHandle),
    Field('orientation', tString, 'horizontal'),
    ])
