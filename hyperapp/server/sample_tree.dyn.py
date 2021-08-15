import logging

from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    )
from hyperapp.common.module import Module

from . import htypes
from .tree import tree_item_t
from .record import record_t

log = logging.getLogger(__name__)


class TreeServant:

    def __init__(self, mosaic, item_t, article_service_factory):
        self._mosaic = mosaic
        self._item_t = item_t
        self._article_service_factory = article_service_factory

    def get(self, request, path):
        log.info("TreeServant.get(%s)", path)
        if path:
            base = path[-1] * 10
        else:
            base = 0
        return [
            self._item_t(base + 1, 'first item'),
            self._item_t(base + 2, 'second item'),
            self._item_t(base + 3, 'third item'),
            self._item_t(base + 4, 'forth item'),
            self._item_t(base + 5, 'fifth item'),
            ]

    def open(self, request, item_key):
        log.info("TreeServant.open(%r)", item_key)
        text = "Opened item: {}".format(item_key)
        piece = text
        return self._mosaic.put(piece)

    def view(self, request, item_key):
        log.info("TreeServant.view(%r)", item_key)
        piece = htypes.sample_tree.article(
            title=f"Article {item_key}",
            text=f"Sample contents for:\n{item_key}",
            )
        return self._mosaic.put(piece)

    def edit(self, request, item_key):
        log.info("TreeServant.edit(%r)", item_key)
        service = self._article_service_factory(item_key)
        return self._mosaic.put(service)


class ArticleServant:

    def __init__(self, rec_t):
        self._rec_t = rec_t

    def get(self, request, article_path):
        log.info("ArticleServant.get(%s)", article_path)
        return self._rec_t(
            title=f"Article {article_path}",
            text=f"Some text for article {article_path}\nwith second line",
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic
        types = services.types

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        int_t_ref = types.reverse_resolve(tInt)
        string_t_ref = types.reverse_resolve(tString)
        int_list_t = TList(tInt)
        int_list_t_ref = types.reverse_resolve(int_list_t)

        tree_object_id = 'test_tree_service_object'
        open_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=int_list_t_ref,
            method_name='open',
            peer_ref=server_peer_ref,
            object_id=tree_object_id,
            )
        edit_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=int_list_t_ref,
            method_name='edit',
            peer_ref=server_peer_ref,
            object_id=tree_object_id,
            )
        view_command = htypes.rpc_command.rpc_element_command(
            key_type_ref=int_list_t_ref,
            method_name='view',
            peer_ref=server_peer_ref,
            object_id=tree_object_id,
            )
        tree_service = htypes.service.tree_service(
            peer_ref=server_peer_ref,
            object_id=tree_object_id,
            dir_list=[[mosaic.put(htypes.sample_tree.sample_tree_d())]],
            param_type_list=[],
            param_list=[],
            command_ref_list=[
                mosaic.put(open_command),
                mosaic.put(view_command),
                mosaic.put(edit_command),
                ],
            key_column_id='key',
            column_list=[
                htypes.service.column('key', int_t_ref),
                htypes.service.column('value', string_t_ref),
                ],
            )

        item_t = tree_item_t(mosaic, types, tree_service)

        article_object_id = 'test_sample_tree_article_service_object'
        article_field_list = [
            htypes.service.record_field('title', string_t_ref),
            htypes.service.record_field('text', string_t_ref),
            ]

        def article_service_factory(path):
            return htypes.service.record_service(
                peer_ref=server_peer_ref,
                object_id=article_object_id,
                dir_list=[[mosaic.put(htypes.sample_tree.sample_tree_article_d())]],
                param_type_list=[
                    htypes.service.param_type('article_path', int_list_t_ref),
                    ],
                param_list=[
                    htypes.service.parameter('article_path', mosaic.put(path, int_list_t)),
                    ],
                command_ref_list=[],
                field_list=article_field_list,
                )

        rec_t = record_t(mosaic, types, article_field_list)

        tree_servant = TreeServant(mosaic, item_t, article_service_factory)
        services.server_rpc_endpoint.register_servant(tree_object_id, tree_servant)
        article_servant = ArticleServant(rec_t)
        services.server_rpc_endpoint.register_servant(article_object_id, article_servant)

        services.server_ref_list.add_ref('samle_tree', 'Sample tree', mosaic.put(tree_service))
