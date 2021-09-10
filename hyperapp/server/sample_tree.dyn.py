import logging

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class TreeServant:

    def __init__(self, mosaic, article_service_factory):
        self._mosaic = mosaic
        self._article_service_factory = article_service_factory

    def get_items(self, request, path):
        log.info("TreeServant.get_items(%s)", path)
        if path:
            base = path[-1] * 10
        else:
            base = 0
        return [
            htypes.sample_tree.item(base + 1, 'first item'),
            htypes.sample_tree.item(base + 2, 'second item'),
            htypes.sample_tree.item(base + 3, 'third item'),
            htypes.sample_tree.item(base + 4, 'forth item'),
            htypes.sample_tree.item(base + 5, 'fifth item'),
            ]

    def describe(self, request, item_key):
        log.info("TreeServant.describe(%r)", item_key)
        text = "Opened item: {}".format(item_key)
        piece = text
        return self._mosaic.put(piece)

    def raw(self, request, item_key):
        log.info("TreeServant.raw(%r)", item_key)
        piece = htypes.sample_tree.article(
            title=f"Article {item_key}",
            text=f"Sample contents for:\n{item_key}",
            )
        return self._mosaic.put(piece)

    def open(self, request, item_key):
        log.info("TreeServant.open(%r)", item_key)
        service = self._article_service_factory(item_key)
        return self._mosaic.put(service)


class ArticleServant:

    def get(self, article_path, request):
        log.info("ArticleServant.get(%s)", article_path)
        return htypes.sample_tree.article(
            title=f"Article {article_path}",
            text=f"Some text for article {article_path}\nwith second line",
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        tree_servant_name = 'sample_tree_servant'
        tree_servant_path = services.servant_path().registry_name(tree_servant_name)

        describe_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=tree_servant_path.get_attr('describe').as_data(services.mosaic),
            name='describe',
            )
        open_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=tree_servant_path.get_attr('open').as_data(services.mosaic),
            name='open',
            )
        raw_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=tree_servant_path.get_attr('raw').as_data(services.mosaic),
            name='raw',
            )
        tree_service = htypes.service.tree_service(
            peer_ref=server_peer_ref,
            servant_path=tree_servant_path.get_attr('get_items').as_data(services.mosaic),
            dir_list=[[mosaic.put(htypes.sample_tree.sample_tree_d())]],
            command_ref_list=[
                mosaic.put(describe_command),
                mosaic.put(raw_command),
                mosaic.put(open_command),
                ],
            key_column_id='key',
            column_list=item_t_to_column_list(services.types, htypes.sample_tree.item),
            )

        article_servant_name = 'sample_tree_article_servant'
        article_servant_path = services.servant_path().registry_name(article_servant_name)

        def article_service_factory(path):
            return htypes.service.record_service(
                peer_ref=server_peer_ref,
                servant_path=article_servant_path.get_attr('get').partial(path).as_data(services.mosaic),
                dir_list=[[mosaic.put(htypes.sample_tree.sample_tree_article_d())]],
                command_ref_list=[],
                )

        tree_servant = TreeServant(mosaic, article_service_factory)
        services.server_rpc_endpoint.register_servant(tree_servant_name, tree_servant)
        article_servant = ArticleServant()
        services.server_rpc_endpoint.register_servant(article_servant_name, article_servant)

        services.server_ref_list.add_ref('samle_tree', 'Sample tree', mosaic.put(tree_service))
