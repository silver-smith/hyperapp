import logging

from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    list_service_t,
    )
from hyperapp.common.module import Module

from . import htypes
from .list_object import list_row_t

log = logging.getLogger(__name__)


class Servant:

    def __init__(self, row_t):
        self._row_t = row_t

    def get(self, request):
        log.info("Servant.get is called")
        return [
            self._row_t(1, 'first row'),
            self._row_t(2, 'second row'),
            self._row_t(3, 'third row'),
            ]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

        server_peer_ref = services.mosaic.put(services.server_identity.peer.piece)

        int_t_ref = services.types.reverse_resolve(tInt)
        string_t_ref = services.types.reverse_resolve(tString)
        service_ot = htypes.list_object_type.list_ot(
            command_list=[],
            key_column_id='key',
            column_list=[
                htypes.list_object_type.column('key', int_t_ref),
                htypes.list_object_type.column('value', string_t_ref),
                ],
            )
        service_ot_ref = services.mosaic.put(service_ot)
        row_t = list_row_t(services.mosaic, services.types, service_ot, 'test_list_service')

        object_id = 'test_list_service_object'
        list_service = list_service_t(
            type_ref=service_ot_ref,
            peer_ref=server_peer_ref,
            object_id=object_id,
            key_field='key',
            )

        servant = Servant(row_t)
        services.server_rpc_endpoint.register_servant(object_id, servant)

        services.local_server_ref.save_piece(list_service)
