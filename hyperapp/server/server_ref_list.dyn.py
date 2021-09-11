import logging
from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

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

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        servant_name = 'server_ref_list'
        servant_path = services.servant_path().registry_name(servant_name)

        open_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('open').as_data(mosaic),
            state_attr_list=['current_key'],
            name='open',
            )
        list_service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('get').as_data(mosaic),
            dir_list=[],
            command_ref_list=[
                mosaic.put(open_command),
                ],
            key_column_id='id',
            column_list=item_t_to_column_list(services.types, htypes.server_ref_list.row),
            )


        ref_list = RefList()
        servant = RefListServant(services.web, ref_list)
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list = ref_list
        services.local_server_ref.save_piece(list_service)
