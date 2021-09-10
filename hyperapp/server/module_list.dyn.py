import logging

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class Servant:

    def __init__(self, web, local_code_module_registry):
        self._web = web
        self._local_code_module_registry = local_code_module_registry

    def list(self, request):
        log.info("Servant.list()")
        item_list = []
        for module_name, rec in self._local_code_module_registry.items():
            module = self._web.summon(rec.module_ref)
            item = htypes.module_list.item(module_name, rec.module_ref, module.file_path)
            item_list.append(item)
        return item_list


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        servant_name = 'module_list'
        servant_path = services.servant_path().registry_name(servant_name)

        service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('list').as_data(services.mosaic),
            dir_list=[[mosaic.put(htypes.module_list.module_list_d())]],
            command_ref_list=[],
            key_column_id='module_name',
            column_list=item_t_to_column_list(services.types, htypes.module_list.item),
            )

        servant = Servant(services.web, services.local_code_module_registry)
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list.add_ref('module_list', 'Module list', mosaic.put(service))
