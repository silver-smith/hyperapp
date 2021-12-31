import logging
from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


RefItem = namedtuple('Item', 'title ref')


class RefList:

    def __init__(self):
        self._item_by_id = {}  # id -> RefItem list

    def add_ref(self, id, title, ref):
        self._item_by_id[id] = RefItem(title, ref)

    def get_ref(self, id):
        return self._item_by_id[id].ref

    def items(self):
        return self._item_by_id.items()


class RefListServant:

    def __init__(self, web, ref_list):
        self._web = web
        self._ref_list = ref_list

    def get(self, request):
        log.info("RefListServant.get()")
        return [
            htypes.server_ref_list.row(id, item.title, item.ref)
            for id, item in self._ref_list.items()
            ]

    def open(self, request, current_key):
        log.info("RefListServant.open(%r)", current_key)
        ref = self._ref_list.get_ref(current_key)
        return self._web.summon(ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        server_ref_list_service = services.resource_module_registry['server.server_ref_list'].make('server_ref_list_service')
        services.local_server_ref.save_piece(server_ref_list_service)
