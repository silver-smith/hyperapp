import logging

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class ListServant:

    def __init__(self, article_service_factory):
        self._article_service_factory = article_service_factory

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
        return self._article_service_factory(current_key)


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

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        list_servant_name = 'sample_list_servant'
        list_servant_path = services.servant_path().registry_name(list_servant_name)

        describe_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('describe').as_data,
            state_attr_list=['current_key'],
            name='describe',
            )
        raw_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('raw').as_data,
            state_attr_list=['current_key'],
            name='raw',
            )
        open_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('open').as_data,
            state_attr_list=['current_key'],
            name='open',
            )
        list_service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('list').as_data,
            dir_list=[[mosaic.put(htypes.sample_list.sample_list_d())]],
            command_ref_list=[
                mosaic.put(describe_command),
                mosaic.put(raw_command),
                mosaic.put(open_command),
                ],
            key_column_id='key',
            column_list=item_t_to_column_list(services.types, htypes.sample_list.row),
            )

        article_servant_name = 'sample_list_article_servant'
        article_servant_path = services.servant_path().registry_name(article_servant_name)

        def article_service_factory(article_id):
            return htypes.service.record_service(
                peer_ref=server_peer_ref,
                servant_path=article_servant_path.get_attr('get').partial(article_id).as_data,
                dir_list=[[mosaic.put(htypes.sample_list.sample_list_article_d())]],
                command_ref_list=[],
                )

        list_servant = ListServant(article_service_factory)
        services.server_rpc_endpoint.register_servant(list_servant_name, list_servant)

        article_servant = ArticleServant()
        services.server_rpc_endpoint.register_servant(article_servant_name, article_servant)

        services.server_ref_list.add_ref('sample_list', 'Sample list', mosaic.put(list_service))
