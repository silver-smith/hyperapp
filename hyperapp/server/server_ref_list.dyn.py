import logging
from collections import namedtuple

from hyperapp.common.htypes import tString, ref_t
from hyperapp.common.module import Module

from . import htypes
from .list import row_t_to_column_list

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

    def __init__(self, mosaic, ref_list):
        self._mosaic = mosaic
        self._ref_list = ref_list

    def get(self, request):
        log.info("RefListServant.get()")
        return [
            htypes.server_ref_list.row(id, item.title, item.ref)
            for id, item in self._ref_list.items()
            ]

    def open(self, request, item_key):
        log.info("RefListServant.open(%r)", item_key)
        return self._ref_list.get_ref(item_key)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic
        types = services.types

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        ref_t_ref = types.reverse_resolve(ref_t)
        string_t_ref = types.reverse_resolve(tString)

        servant_name = 'server_ref_list'
        servant_path = services.servant_path().registry_name(servant_name).get_attr('get')

        open_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.as_data(services.mosaic),
            name='open',
            key_type_ref=string_t_ref,
            )
        list_service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=servant_path.as_data(services.mosaic),
            dir_list=[],
            command_ref_list=[
                mosaic.put(open_command),
                ],
            key_column_id='id',
            column_list=row_t_to_column_list(services.types, htypes.server_ref_list.row),
            )


        ref_list = RefList()
        servant = RefListServant(mosaic, ref_list)
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list = ref_list
        services.local_server_ref.save_piece(list_service)
