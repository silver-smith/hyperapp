import logging

from .services import (
    mosaic,
    )
from .code.service_ctr import ServiceTemplateCtr
from .code.system_probe import SystemProbe

log = logging.getLogger(__name__)


class SystemJob:

    def __init__(self, cfg_item_creg, system_config_piece):
        self._cfg_item_creg = cfg_item_creg  # Used only from 'run' method, inside job process.
        self._system_config_piece = system_config_piece  # --//--

    def _configure_system(self, system, resource_list):
        for resource in resource_list:
            resource.configure_system(system)

    def _prepare_system(self, resources):
        system = SystemProbe()
        system.load_config(self._system_config_piece)
        self._configure_system(system, resources)
        system.migrate_globals()
        _ = system.resolve_service('marker_registry')
        return system

    def _enum_constructor_refs(self, system, ctr_collector):
        for name, rec in system.resolved_templates.items():
            log.info("Resolved service %s: %s", name, rec)
            ctr = ServiceTemplateCtr.from_rec(name, rec)
            yield mosaic.put(ctr.piece)
        for ctr in ctr_collector.constructors:
            yield mosaic.put(ctr.piece)
