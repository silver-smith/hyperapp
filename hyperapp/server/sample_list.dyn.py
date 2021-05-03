import logging

from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    service_command_t,
    list_service_t,
    )
from hyperapp.common.module import Module

from . import htypes
from .list_object import list_row_t

log = logging.getLogger(__name__)


class Servant:

    def __init__(self, mosaic, row_t):
        self._mosaic = mosaic
        self._row_t = row_t

    def get(self, request):
        log.info("Servant.get is called")
        return [
            self._row_t(1, 'first row'),
            self._row_t(2, 'second row'),
            self._row_t(3, 'third row'),
            ]

    def open(self, request, item_key):
        log.info("Servant.open(%r) is called", item_key)
        text = "Opened item: {}".format(item_key)
        piece = text
        return self._mosaic.put(piece)

    def edit(self, request, item_key):
        log.info("Servant.edit(%r) is called", item_key)
        piece = htypes.sample_list.article(
            title=f"Article {item_key}",
            text=f"Sample contents for:\n{item_key}",
            )
        return self._mosaic.put(piece)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

        server_peer_ref = services.mosaic.put(services.server_identity.peer.piece)

        int_t_ref = services.types.reverse_resolve(tInt)
        string_t_ref = services.types.reverse_resolve(tString)
        service_ot = htypes.list_object_type.list_ot(
            command_list=[
                htypes.object_type.object_command('open', None),
                htypes.object_type.object_command('edit', None),
                ],
            key_column_id='key',
            column_list=[
                htypes.list_object_type.column('key', int_t_ref),
                htypes.list_object_type.column('value', string_t_ref),
                ],
            )
        service_ot_ref = services.mosaic.put(service_ot)
        row_t = list_row_t(services.mosaic, services.types, service_ot)

        object_id = 'test_list_service_object'
        open_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=services.types.reverse_resolve(tInt),
            method_name='open',
            peer_ref=server_peer_ref,
            object_id=object_id,
            )
        edit_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=services.types.reverse_resolve(tInt),
            method_name='edit',
            peer_ref=server_peer_ref,
            object_id=object_id,
            )
        list_service = list_service_t(
            type_ref=service_ot_ref,
            peer_ref=server_peer_ref,
            object_id=object_id,
            command_list=[
                service_command_t('open', services.mosaic.put(open_command)),
                service_command_t('edit', services.mosaic.put(edit_command)),
                ],
            )

        servant = Servant(services.mosaic, row_t)
        services.server_rpc_endpoint.register_servant(object_id, servant)

        services.local_server_ref.save_piece(list_service)
