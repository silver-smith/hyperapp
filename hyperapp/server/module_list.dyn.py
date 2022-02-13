import logging
from functools import cached_property, partial

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class Servant:

    def __init__(self, mosaic, web, local_modules, module_registry, status_filter):
        self._mosaic = mosaic
        self._web = web
        self._local_modules = local_modules
        self._module_registry = module_registry
        self._status_filter = status_filter

    # Should be populated only after all modules are imported, otherwise not-yet imported modules are shown as available.
    @cached_property
    def _name_to_item(self):
        name_to_item = {}
        imported_names = {rec.name for rec in self._module_registry.elements()}
        for module_name, module in self._local_modules.by_name.items():
            module_ref = self._mosaic.put(module)
            if module_name in imported_names:
                status = 'imported'
            else:
                status = 'available'
            name_to_item[module_name] = htypes.module_list.item(
                module_name, module_ref, module.file_path, status)
        return name_to_item

    def list(self, request):
        log.info("Servant(%s).list", self._status_filter)
        return list(
            item for item
            in self._name_to_item.values()
            if item.status in self._status_filter
            )

    def open(self, request, current_key):
        item = self._name_to_item[current_key]
        return self._web.summon(item.module_ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_ref_list_piece = services.resource_module_registry['server.server_ref_list']['server_ref_list']
        server_ref_list = services.python_object_creg.animate(server_ref_list_piece)

        all_module_list_service_piece = services.resource_module_registry['server.module_list']['all_module_list_service']
        available_module_list_service_piece = services.resource_module_registry['server.module_list']['available_module_list_service']
        imported_module_list_service_piece = services.resource_module_registry['server.module_list']['imported_module_list_service']

        all_module_list_service = services.python_object_creg.animate(all_module_list_service_piece)
        available_module_list_service = services.python_object_creg.animate(available_module_list_service_piece)
        imported_module_list_service = services.python_object_creg.animate(imported_module_list_service_piece)

        server_ref_list.add_ref('all_module_list', 'Module list', mosaic.put(all_module_list_service))
        server_ref_list.add_ref('available_module_list', 'Available modules', mosaic.put(available_module_list_service))
        server_ref_list.add_ref('imported_module_list', 'Imported modules', mosaic.put(imported_module_list_service))
