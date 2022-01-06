import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class TreeServant:

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

    def describe(self, request, current_key):
        log.info("TreeServant.describe(%r)", current_key)
        return "Opened item: {}".format(current_key)

    def raw(self, request, current_key):
        log.info("TreeServant.raw(%r)", current_key)
        return htypes.sample_tree.article(
            title=f"Article {current_key}",
            text=f"Sample contents for:\n{current_key}",
            )

    def open(self, request, current_key):
        log.info("TreeServant.open(%r)", current_key)
        return htypes.sample_tree.sample_article(article_path=current_key)


class ArticleServant:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.article_path)

    def __init__(self, article_path):
        self._article_path = article_path

    def get(self, request):
        log.info("ArticleServant(%s).get", self._article_path)
        return htypes.sample_tree.article(
            title=f"Article {self._article_path}",
            text=f"Some text for article {self._article_path}\nwith second line",
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        services.python_object_creg.register_actor(htypes.sample_tree.sample_article, ArticleServant.from_piece)

        server_ref_list_piece = services.resource_module_registry['server.server_ref_list'].make('server_ref_list')
        server_ref_list = services.python_object_creg.animate(server_ref_list_piece)
        sample_tree_service = services.resource_module_registry['server.sample_tree'].make('sample_tree_service')
        server_ref_list.add_ref('sample_tree', 'Sample tree', mosaic.put(sample_tree_service))

        services.piece_service_registry[htypes.sample_tree.sample_article] = htypes.map_service.record_service(
            dir_list=[[mosaic.put(htypes.sample_tree.sample_tree_article_d())]],
            command_ref_list=[],
            )
