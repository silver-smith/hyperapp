from ..htypes import tInt, tString, Field, TList, tHandle, tViewHandle


tSplitterHandle = tHandle.register('splitter', base=tViewHandle, fields=[
    Field('x', tHandle),
    Field('y', tHandle),
    Field('orientation', tString, 'horizontal'),
    Field('focused', tInt, 0),  # 0 or 1
    Field('sizes', TList(tInt), []),
    ])
