import logging

from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    )
from hyperapp.common.module import Module

from . import htypes
from .list import list_row_t
from .record import record_t

log = logging.getLogger(__name__)


class ListServant:

    def __init__(self, mosaic, row_t, record_service_factory):
        self._mosaic = mosaic
        self._row_t = row_t
        self._record_service_factory = record_service_factory

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
        service = self._record_service_factory(item_key)
        return self._mosaic.put(service)


class RecordServant:

    def __init__(self, rec_t):
        self._rec_t = rec_t

    def get(self, request, article_id):
        log.info("RecordServant.get(%s)", article_id)
        return self._rec_t(
            title=f"Article {article_id}",
            text=f"Some text for article {article_id}\nwith second line",
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic
        types = services.types

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        int_t_ref = types.reverse_resolve(tInt)
        string_t_ref = types.reverse_resolve(tString)

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
        row_t = list_row_t(mosaic, types, list_service_ot)

        list_object_id = 'test_list_service_object'
        open_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=int_t_ref,
            method_name='open',
            peer_ref=server_peer_ref,
            object_id=list_object_id,
            )
        edit_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=int_t_ref,
            method_name='edit',
            peer_ref=server_peer_ref,
            object_id=list_object_id,
            )
        view_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=int_t_ref,
            method_name='view',
            peer_ref=server_peer_ref,
            object_id=list_object_id,
            )
        list_service = htypes.service.list_service(
            type_ref=mosaic.put(list_service_ot),
            peer_ref=server_peer_ref,
            object_id=list_object_id,
            param_type_list=[],
            param_list=[],
            command_list=[
                htypes.service.command('open', mosaic.put(open_command)),
                htypes.service.command('view', mosaic.put(view_command)),
                htypes.service.command('edit', mosaic.put(edit_command)),
                ],
            )

        record_object_id = 'test_record_service_object'
        string_ot_ref = mosaic.put(htypes.string_ot.string_ot(command_list=[]))
        record_service_ot = htypes.record_ot.record_ot(
            command_list=[],
            field_type_list=[
                htypes.record_ot.field('title', string_ot_ref),
                htypes.record_ot.field('text', string_ot_ref),
                ],
            )
        record_field_list = [
            htypes.service.record_field('title', string_t_ref),
            htypes.service.record_field('text', string_t_ref),
            ]

        def record_service_factory(article_id):
            return htypes.service.record_service(
                type_ref=mosaic.put(record_service_ot),
                peer_ref=server_peer_ref,
                object_id=record_object_id,
                param_type_list=[
                    htypes.service.param_type('article_id', int_t_ref),
                    ],
                param_list=[
                    htypes.service.parameter('article_id', mosaic.put(article_id)),
                    ],
                command_list=[],
                field_list=record_field_list,
                )

        rec_t = record_t(mosaic, types, record_field_list)

        list_servant = ListServant(mosaic, row_t, record_service_factory)
        services.server_rpc_endpoint.register_servant(list_object_id, list_servant)
        record_servant = RecordServant(rec_t)
        services.server_rpc_endpoint.register_servant(record_object_id, record_servant)

        services.server_ref_list.add_ref('samle_list', 'Sample list', mosaic.put(list_service))
