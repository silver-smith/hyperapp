import logging

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class Servant:

    def __init__(self, web, service, selector):
        self._web = web
        self._service = service
        self._selector = selector
        self._name_to_item = {}

    def list(self, request):
        return list(self._name_to_item.values())

    def open(self, request, current_key):
        item = self._name_to_item[current_key]
        return self._web.summon(item.module_ref)

    def select_module(self, request):
        return self._selector

    def set_module(self, request, module_name, module_ref):
        log.info("Set module: %r %s", module_name, module_ref)
        self._name_to_item[module_name] = htypes.htest_list.item(module_name, module_ref)
        return self._service


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        servant_name = 'htest_list'
        servant_path = services.servant_path().registry_name(servant_name)

        open_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('open').as_data(services.mosaic),
            state_attr_list=['current_key'],
            name='open',
            )
        select_module_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('select_module').as_data(services.mosaic),
            state_attr_list=[],
            name='select_module',
            )
        service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('list').as_data(services.mosaic),
            dir_list=[[mosaic.put(htypes.htest_list.htest_list_d())]],
            command_ref_list=[
                mosaic.put(open_command),
                mosaic.put(select_module_command),
                ],
            key_column_id='module_name',
            column_list=item_t_to_column_list(services.types, htypes.htest_list.item),
            )

        module_list_servant_name = 'module_list'
        module_list_servant_path = services.servant_path().registry_name(module_list_servant_name)
        module_list_service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=module_list_servant_path.get_attr('list').partial('available').as_data(services.mosaic),
            dir_list=[[mosaic.put(htypes.module_list.module_list_d())]],
            command_ref_list=[],
            key_column_id='module_name',
            column_list=item_t_to_column_list(services.types, htypes.module_list.item),
            )

        rpc_callback = htypes.rpc_callback.rpc_callback(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('set_module').as_data(services.mosaic),
            item_attr_list=['module_name', 'module_ref'],
            )
        selector = htypes.selector.selector(
            list_ref=mosaic.put(module_list_service),
            callback_ref=mosaic.put(rpc_callback),
            )

        servant = Servant(services.web, service, selector)
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list.add_ref('htest_list', 'Test list', mosaic.put(service))
