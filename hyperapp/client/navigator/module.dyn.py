from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    Field,
    TRecord,
    )
from hyperapp.client.module import ClientModule
from .history_list import HistoryList
from .navigator import NavigatorView


MODULE_NAME = 'navigator'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.view_registry.register('navigator', NavigatorView.from_state, services.view_registry)
        services.objimpl_registry.register(HistoryList.impl_id, HistoryList.from_state)
