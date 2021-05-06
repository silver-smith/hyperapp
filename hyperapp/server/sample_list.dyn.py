import logging

from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    service_command_t,
    list_service_t,
    record_field_t,
    record_service_t,
    )
from hyperapp.common.module import Module

from . import htypes
from .list_object import list_row_t
from .record import record_t

log = logging.getLogger(__name__)


class ListServant:

    def __init__(self, mosaic, row_t, record_service):
        self._mosaic = mosaic
        self._row_t = row_t
        self._record_service = record_service

    def get(self, request):
        log.info("ListServant.get()")
        return [
            self._row_t(1, 'first row'),
            self._row_t(2, 'second row'),
            self._row_t(3, 'third row'),
            ]

    def open(self, request, item_key):
        log.info("ListServant.open(%r)", item_key)
        text = "Opened item: {}".format(item_key)
        piece = text
        return self._mosaic.put(piece)

    def view(self, request, item_key):
        log.info("ListServant.view(%r)", item_key)
        piece = htypes.sample_list.article(
            title=f"Article {item_key}",
            text=f"Sample contents for:\n{item_key}",
            )
        return self._mosaic.put(piece)

    def edit(self, request, item_key):
        log.info("ListServant.edit(%r)", item_key)
        return self._mosaic.put(self._record_service)


class RecordServant:

    def __init__(self, rec_t):
        self._rec_t = rec_t

    def get(self, request):
        log.info("RecordServant.get()")
        return self._rec_t(
            title="Some title",
            text="Some text\nwith second line",
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        server_peer_ref = services.mosaic.put(services.server_identity.peer.piece)

        int_t_ref = services.types.reverse_resolve(tInt)
        string_t_ref = services.types.reverse_resolve(tString)

        list_service_ot = htypes.list_ot.list_ot(
            command_list=[
                htypes.object_type.object_command('open', None),
                htypes.object_type.object_command('view', None),
                htypes.object_type.object_command('edit', None),
                ],
            key_column_id='key',
            column_list=[
                htypes.list_ot.column('key', int_t_ref),
                htypes.list_ot.column('value', string_t_ref),
                ],
            )
        row_t = list_row_t(services.mosaic, services.types, list_service_ot)

        list_object_id = 'test_list_service_object'
        open_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=services.types.reverse_resolve(tInt),
            method_name='open',
            peer_ref=server_peer_ref,
            object_id=list_object_id,
            )
        edit_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=services.types.reverse_resolve(tInt),
            method_name='edit',
            peer_ref=server_peer_ref,
            object_id=list_object_id,
            )
        view_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=services.types.reverse_resolve(tInt),
            method_name='view',
            peer_ref=server_peer_ref,
            object_id=list_object_id,
            )
        list_service = list_service_t(
            type_ref=services.mosaic.put(list_service_ot),
            peer_ref=server_peer_ref,
            object_id=list_object_id,
            command_list=[
                service_command_t('open', services.mosaic.put(open_command)),
                service_command_t('view', services.mosaic.put(view_command)),
                service_command_t('edit', services.mosaic.put(edit_command)),
                ],
            )

        record_object_id = 'test_record_service_object'
        string_ot_ref = services.mosaic.put(htypes.string.string_ot(command_list=[]))
        record_service_ot = htypes.record_ot.record_ot(
            command_list=[],
            field_type_list=[
                htypes.record_ot.field('title', string_ot_ref),
                htypes.record_ot.field('text', string_ot_ref),
                ],
            )
        record_field_list = [
            record_field_t('title', string_t_ref),
            record_field_t('text', string_t_ref),
            ]
        record_service = record_service_t(
            type_ref=services.mosaic.put(record_service_ot),
            peer_ref=server_peer_ref,
            object_id=record_object_id,
            command_list=[],
            field_list=record_field_list,
            )
        rec_t = record_t(services.mosaic, services.types, record_field_list)

        list_servant = ListServant(services.mosaic, row_t, record_service)
        services.server_rpc_endpoint.register_servant(list_object_id, list_servant)
        record_servant = RecordServant(rec_t)
        services.server_rpc_endpoint.register_servant(record_object_id, record_servant)

        services.local_server_ref.save_piece(list_service)
