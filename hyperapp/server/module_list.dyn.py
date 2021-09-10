import logging

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class Servant:

    def __init__(self, web, available_code_modules, imported_code_modules):
        self._web = web
        self._name_to_item = {}
        for module_name, module_ref in available_code_modules.items():
            module = web.summon(module_ref)
            if module_name in imported_code_modules:
                status = 'imported'
            else:
                status = 'available'
            self._name_to_item[module_name] = htypes.module_list.item(
                module_name, module_ref, module.file_path, status)

    def list(self, status_filter, request):
        log.info("Servant.list(%s)", status_filter)
        return list(
            item for item
            in self._name_to_item.values()
            if item.status in status_filter
            )

    def open(self, request, current_key):
        item = self._name_to_item[current_key]
        return self._web.summon(item.module_ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        servant_name = 'module_list'
        servant_path = services.servant_path().registry_name(servant_name)

        open_command = htypes.rpc_command.rpc_element_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('open').as_data(services.mosaic),
            name='open',
            )

        def service(status_filter):
            return htypes.service.list_service(
                peer_ref=server_peer_ref,
                servant_path=servant_path.get_attr('list').partial(status_filter).as_data(services.mosaic),
                dir_list=[[mosaic.put(htypes.module_list.module_list_d())]],
                command_ref_list=[
                    mosaic.put(open_command),
                    ],
                key_column_id='module_name',
                column_list=item_t_to_column_list(services.types, htypes.module_list.item),
                )

        servant = Servant(services.web, services.available_code_modules, services.imported_code_modules)
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list.add_ref('all_module_list', 'Module list', mosaic.put(service(['imported', 'available'])))
        services.server_ref_list.add_ref('imported_module_list', 'Imported modules', mosaic.put(service(['imported'])))
        services.server_ref_list.add_ref('available_module_list', 'Available modules', mosaic.put(service(['available'])))
