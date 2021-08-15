import logging
from collections import namedtuple

from hyperapp.common.htypes import tString, ref_t
from hyperapp.common.module import Module

from . import htypes
from .list import list_row_t

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

    def __init__(self, mosaic, row_t, ref_list):
        self._mosaic = mosaic
        self._row_t = row_t
        self._ref_list = ref_list

    def get(self, request):
        log.info("RefListServant.get()")
        return [
            self._row_t(id, item.title, item.ref)
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

        object_id = 'server_ref_list'
        open_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=string_t_ref,
            method_name='open',
            peer_ref=server_peer_ref,
            object_id=object_id,
            )
        list_service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            object_id=object_id,
            dir_list=[],
            param_type_list=[],
            param_list=[],
            command_ref_list=[
                mosaic.put(open_command),
                ],
            key_column_id='id',
            column_list=[
                htypes.service.column('id', string_t_ref),
                htypes.service.column('title', string_t_ref),
                htypes.service.column('ref', ref_t_ref),
                ],
            )

        row_t = list_row_t(mosaic, types, list_service)

        ref_list = RefList()
        servant = RefListServant(mosaic, row_t, ref_list)
        services.server_rpc_endpoint.register_servant(object_id, servant)

        services.server_ref_list = ref_list
        services.local_server_ref.save_piece(list_service)
