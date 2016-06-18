from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    Field,
    TRecord,
    tObject,
    tBaseObject,
    tHandle,
    tViewHandle,
    list_handle_type,
    )


item_type = TRecord([
    Field('title', tString),
    Field('handle', tHandle),
    ])

state_type = tHandle.register('navigator', base=tViewHandle, fields=[
    Field('history', TList(item_type)),
    Field('current_pos', tInt),
    ])

history_list_type = tObject.register('history_list', base=tBaseObject, fields=[
    Field('history', TList(item_type)),
    ])

history_list_handle_type = list_handle_type('history_list', tInt)
