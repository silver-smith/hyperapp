from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    Field,
    TRecord,
    )
from ..module import ClientModule
from .navigator import View
from .history_list import HistoryList


MODULE_NAME = 'navigator'


this_module = None

def get_this_module():
    return this_module


class ThisModule(ClientModule):

    def __init__(self, services):
        global this_module
        core_types = services.types.core
        super().__init__(MODULE_NAME, services)
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
        #self.history_list_handle_type = list_handle_type(core_types, tInt)
        this_module = self
        services.view_registry.register('navigator', View.from_state, services.view_registry, self)
        services.objimpl_registry.register(HistoryList.impl_id, HistoryList.from_state, self)
