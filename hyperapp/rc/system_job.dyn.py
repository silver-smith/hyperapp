import logging
from itertools import groupby

from .services import (
    mosaic,
    )
from .code.config_ctl import service_pieces_to_config
from .code.service_ctr import ServiceTemplateCtr
from .code.system_probe import SystemProbe

log = logging.getLogger(__name__)


class SystemJob:

    def __init__(self, cfg_item_creg, system_config_piece):
        self._cfg_item_creg = cfg_item_creg  # Used only from 'run' method, inside job process.
        self._system_config_piece = system_config_piece  # --//--

    def _resource_group(self, resource):
        if resource.is_system_resource:
            return 0
        if resource.is_service_resource:
            return 1
        return 2

    def _compose_resources_config(self, system, resource_list):
        config_ctl = system.resolve_service('config_ctl')
        service_to_config_piece = {}
        for resource in resource_list:
            for service_name, item_list in resource.system_config_items.items():
                ctl = config_ctl[service_name]
                config_piece = ctl.item_pieces_to_data(item_list)
                service_to_config_piece[service_name] = config_piece
        return service_pieces_to_config(service_to_config_piece)

    def _apply_resources_config(self, system, unsorted_resource_list):
        sorted_resource_list = sorted(unsorted_resource_list, key=self._resource_group)
        resource_list_list = [
            list(resource_it)
            for _, resource_it in groupby(sorted_resource_list, self._resource_group)
            ]
        for resource_list in resource_list_list:
            config = self._compose_resources_config(system, resource_list)
            system.load_config(config)
        # config = self._compose_resources_config(system, unsorted_resource_list)
        # system.load_config(config)

    def _configure_system(self, system, resource_list):
        sorted_resource_list = sorted(resource_list, key=self._resource_group)
        for resource in sorted_resource_list:
            resource.configure_system(system)

    def _prepare_system(self, resources):
        system = SystemProbe()
        system.load_config(self._system_config_piece)
        self._apply_resources_config(system, resources)
        self._configure_system(system, resources)
        system.migrate_globals()
        _ = system.resolve_service('marker_registry')
        return system

    def _enum_constructor_refs(self, ctr_collector):
        for ctr in ctr_collector.constructors:
            yield mosaic.put(ctr.piece)
