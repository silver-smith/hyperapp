import logging
from functools import cached_property, partial

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class Servant:

    def __init__(self, web, local_modules, module_registry):
        self._web = web
        self._local_modules = local_modules
        self._module_registry = module_registry

    # Should be populated only after all modules are imported, otherwise not-yet imported modules are shown as available.
    @cached_property
    def _name_to_item(self):
        name_to_item = {}
        imported_names = {rec.name for rec in self._module_registry.elements()}
        for module_name, module_ref in self._local_modules.by_name.items():
            module = self._web.summon(module_ref)
            if module_name in imported_names:
                status = 'imported'
            else:
                status = 'available'
            name_to_item[module_name] = htypes.module_list.item(
                module_name, module_ref, module.file_path, status)
        return name_to_item

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

        open_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('open').as_data,
            state_attr_list=['current_key'],
            name='open',
            )

        def service_factory(status_filter, with_open_command=True):
            if with_open_command:
                command_ref_list = [
                    mosaic.put(open_command),
                    ]
            else:
                command_ref_list = []
            return htypes.service.list_service(
                peer_ref=server_peer_ref,
                servant_path=servant_path.get_attr('list').partial(status_filter).as_data,
                dir_list=[[mosaic.put(htypes.module_list.module_list_d())]],
                command_ref_list=command_ref_list,
                key_column_id='module_name',
                column_list=item_t_to_column_list(services.types, htypes.module_list.item),
                )

        servant = Servant(services.web, services.local_modules, services.module_registry)
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list.add_ref('all_module_list', 'Module list', mosaic.put(service_factory(['imported', 'available'])))
        services.server_ref_list.add_ref('imported_module_list', 'Imported modules', mosaic.put(service_factory(['imported'])))
        services.server_ref_list.add_ref('available_module_list', 'Available modules', mosaic.put(service_factory(['available'])))

        services.module_list_service_factory = partial(service_factory, with_open_command=False)
