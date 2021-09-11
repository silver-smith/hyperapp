import logging

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class Servant:

    def __init__(self):
        self._name_to_item = {}

    def list(self, request):
        log.info("Servant.list()")
        return list(self._name_to_item.values())

    def open(self, request, current_key):
        item = self._name_to_item[current_key]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        servant_name = 'htest_list'
        servant_path = services.servant_path().registry_name(servant_name)

        open_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('open').as_data(services.mosaic),
            name='open',
            )
        service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('list').as_data(services.mosaic),
            dir_list=[[mosaic.put(htypes.htest_list.htest_list_d())]],
            command_ref_list=[
                mosaic.put(open_command),
                ],
            key_column_id='module_name',
            column_list=item_t_to_column_list(services.types, htypes.htest_list.item),
            )

        servant = Servant()
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list.add_ref('htest_list', 'Test list', mosaic.put(service))
