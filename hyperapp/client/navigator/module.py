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
from ..module import Module


this_module = None

def get_this_module():
    return this_module


class ThisModule(Module):

    def __init__( self, services ):
        global this_module
        Module.__init__(self, services)
        self.item_type = TRecord([
            Field('title', tString),
            Field('handle', tHandle),
            ])
        self.state_type = tHandle.register('navigator', base=tViewHandle, fields=[
            Field('history', TList(self.item_type)),
            Field('current_pos', tInt),
            ])
        self.history_list_type = tObject.register('history_list', base=tBaseObject, fields=[
            Field('history', TList(self.item_type)),
            ])
        self.history_list_handle_type = list_handle_type('history_list', tInt)
        this_module = self
