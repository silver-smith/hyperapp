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


class ArticleServant:

    def get(self, article_id, request):
        log.info("ArticleServant.get(%s)", article_id)
        return htypes.sample_list.article(
            title=f"Article {article_id}",
            text=f"Some text for article {article_id}\nwith second line",
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        # def article_service_factory(article_id):
        #     return htypes.service.record_service(
        #         peer_ref=server_peer_ref,
        #         servant_path=article_servant_path.get_attr('get').partial(article_id).as_data,
        #         dir_list=[[mosaic.put(htypes.sample_list.sample_list_article_d())]],
        #         command_ref_list=[],
        #         )

        # article_servant = ArticleServant()
        # services.server_rpc_endpoint.register_servant(article_servant_name, article_servant)

        services.python_object_creg.register_actor(htypes.sample_list.sample_list, ListServant.from_piece)

        server_ref_list_piece = services.resource_module_registry['server.server_ref_list'].make('server_ref_list')
        server_ref_list = services.python_object_creg.animate(server_ref_list_piece)
        sample_list_service = services.resource_module_registry['server.sample_list'].make('sample_list_service')
        server_ref_list.add_ref('sample_list', 'Sample list', mosaic.put(sample_list_service))
