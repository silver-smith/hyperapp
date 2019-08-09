from hyperapp.client.module import ClientModule
from .history_list import HistoryList
from .navigator import NavigatorView


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_registry.register('navigator', NavigatorView.from_state, services.view_registry)
        # services.objimpl_registry.register(HistoryList.impl_id, HistoryList.from_state)
