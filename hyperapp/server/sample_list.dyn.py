import logging

from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    )
from hyperapp.common.module import Module

from . import htypes
from .list import row_t_to_column_list
from .record import record_t

log = logging.getLogger(__name__)


class ListServant:

    def __init__(self, mosaic, article_service_factory):
        self._mosaic = mosaic
        self._article_service_factory = article_service_factory

    def list(self, request):
        log.info("ListServant.list()")
        return [
            htypes.sample_list.row(1, 'first row'),
            htypes.sample_list.row(2, 'second row'),
            htypes.sample_list.row(3, 'third row'),
            ]

    def describe(self, request, item_key):
        log.info("ListServant.describe(%r)", item_key)
        text = "Opened item: {}".format(item_key)
        piece = text
        return self._mosaic.put(piece)

    def raw(self, request, item_key):
        log.info("ListServant.raw(%r)", item_key)
        piece = htypes.sample_list.article(
            title=f"Article {item_key}",
            text=f"Sample contents for:\n{item_key}",
            )
        return self._mosaic.put(piece)

    def open(self, request, item_key):
        log.info("ListServant.open(%r)", item_key)
        service = self._article_service_factory(item_key)
        return self._mosaic.put(service)


class ArticleServant:

    def __init__(self, rec_t):
        self._rec_t = rec_t

    def get(self, request, article_id):
        log.info("ArticleServant.get(%s)", article_id)
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

        list_servant_name = 'test_list_service_object'
        list_servant_path = services.servant_path().registry_name(list_servant_name)

        describe_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('describe').as_data(services.mosaic),
            name='describe',
            key_type_ref=int_t_ref,
            )
        raw_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('raw').as_data(services.mosaic),
            name='raw',
            key_type_ref=int_t_ref,
            )
        open_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('open').as_data(services.mosaic),
            name='open',
            key_type_ref=int_t_ref,
            )
        list_service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('list').as_data(services.mosaic),
            dir_list=[[mosaic.put(htypes.sample_list.sample_list_d())]],
            command_ref_list=[
                mosaic.put(describe_command),
                mosaic.put(raw_command),
                mosaic.put(open_command),
                ],
            key_column_id='key',
            column_list=row_t_to_column_list(services.types, htypes.sample_list.row),
            )

        article_object_id = 'test_sample_list_article_service_object'
        article_field_list = [
            htypes.service.record_field('title', string_t_ref),
            htypes.service.record_field('text', string_t_ref),
            ]

        def article_service_factory(article_id):
            return htypes.service.record_service(
                peer_ref=server_peer_ref,
                object_id=article_object_id,
                dir_list=[[mosaic.put(htypes.sample_list.sample_list_article_d())]],
                param_type_list=[
                    htypes.service.param_type('article_id', int_t_ref),
                    ],
                param_list=[
                    htypes.service.parameter('article_id', mosaic.put(article_id)),
                    ],
                command_ref_list=[],
                field_list=article_field_list,
                )

        # rec_t = record_t(mosaic, types, article_field_list)

        list_servant = ListServant(mosaic, article_service_factory)
        services.server_rpc_endpoint.register_servant(list_servant_name, list_servant)
        # article_servant = ArticleServant(rec_t)
        # services.server_rpc_endpoint.register_servant(article_object_id, article_servant)

        services.server_ref_list.add_ref('samle_list', 'Sample list', mosaic.put(list_service))
