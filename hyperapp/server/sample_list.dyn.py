import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class ListServant:

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def list(self, request):
        log.info("ListServant.list()")
        return [
            htypes.sample_list.row(1, 'first row'),
            htypes.sample_list.row(2, 'second row'),
            htypes.sample_list.row(3, 'third row'),
            ]

    def describe(self, request, current_key):
        log.info("ListServant.describe(%r)", current_key)
        return "Opened item: {}".format(current_key)

    def raw(self, request, current_key):
        log.info("ListServant.raw(%r)", current_key)
        return htypes.sample_list.article(
            title=f"Article {current_key}",
            text=f"Sample contents for:\n{current_key}",
            )

    def open(self, request, current_key):
        log.info("ListServant.open(%r)", current_key)
        return htypes.sample_list.sample_article(article_id=current_key)


class ArticleServant:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.article_id)

    def __init__(self, article_id):
        self._article_id = article_id

    def get(self, request):
        log.info("ArticleServant(%s).get", self._article_id)
        return htypes.sample_list.article(
            title=f"Article {self._article_id}",
            text=f"Some text for article {self._article_id}\nwith second line",
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        services.python_object_creg.register_actor(htypes.sample_list.sample_list, ListServant.from_piece)
        services.python_object_creg.register_actor(htypes.sample_list.sample_article, ArticleServant.from_piece)

        server_ref_list_piece = services.resource_module_registry['server.server_ref_list'].make('server_ref_list')
        server_ref_list = services.python_object_creg.animate(server_ref_list_piece)
        sample_list_service = services.resource_module_registry['server.sample_list'].make('sample_list_service')
        server_ref_list.add_ref('sample_list', 'Sample list', mosaic.put(sample_list_service))

        services.piece_service_registry[htypes.sample_list.sample_article] = htypes.map_service.record_service(
            command_ref_list=[],
            )
