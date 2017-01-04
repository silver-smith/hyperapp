from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    Field,
    TRecord,
    list_handle_type,
    )
from ..module import Module


this_module = None

def get_this_module():
    return this_module


class ThisModule(Module):

    def __init__( self, services ):
        global this_module
        core_types = services.core_types
        Module.__init__(self, services)
        self.item_type = TRecord([
            Field('title', tString),
            Field('handle', core_types.handle),
            ])
        self.state_type = core_types.handle.register('navigator', base=core_types.view_handle, fields=[
            Field('history', TList(self.item_type)),
            Field('current_pos', tInt),
            ])
        self.history_list_type = core_types.object.register('history_list', base=core_types.object_base, fields=[
            Field('history', TList(self.item_type)),
            ])
        self.history_list_handle_type = list_handle_type(core_types, 'history_list', tInt)
        this_module = self
