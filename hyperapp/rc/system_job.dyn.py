import logging
from collections import defaultdict
from itertools import groupby

from .services import (
    mosaic,
    )
from .code.config_ctl import (
    item_pieces_to_data,
    service_pieces_to_config,
    merge_system_config_pieces,
    )
from .code.service_ctr import ServiceTemplateCtr
from .code.system_probe import SystemProbe

log = logging.getLogger(__name__)


class SystemJob:

    def __init__(self, system_config_piece):
        self._system_config_piece = system_config_piece  # Used only from 'run' method, inside job process.

    def _resource_group(self, resource):
        if resource.is_system_resource:
            return 0
        if resource.is_service_resource:
            return 1
        return 2

    def _compose_resources_config(self, system, resource_list):
        service_to_items = defaultdict(list)
        for resource in resource_list:
            for service_name, item_list in resource.system_config_items.items():
                service_to_items[service_name] += item_list
        # We expect that later resource items will override former ones.
        for resource in resource_list:
            for service_name, item_list in resource.system_config_items_override.items():
                service_to_items[service_name] += item_list
        service_to_config_piece = {
            service_name: item_pieces_to_data(item_list)
            for service_name, item_list in service_to_items.items()
            }
        return service_pieces_to_config(service_to_config_piece)

    def _configure_system(self, system, resource_list):
        sorted_resource_list = sorted(resource_list, key=self._resource_group)
        for resource in sorted_resource_list:
            resource.configure_system(system)

    def _prepare_system(self, resources):
        system = SystemProbe()
        resources_config = self._compose_resources_config(system, resources)
        config = merge_system_config_pieces(self._system_config_piece, resources_config)
        system.load_config(config)
        self._configure_system(system, resources)
        system.migrate_globals()
        _ = system.resolve_service('marker_registry')  # Init markers.
        return system

    def _enum_constructor_refs(self, ctr_collector):
        for ctr in ctr_collector.constructors:
            yield mosaic.put(ctr.piece)
