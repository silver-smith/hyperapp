from .services import (
    mosaic,
    )
from .code.actor_ctr import ActorTemplateCtr
from .code.service_ctr import ServiceTemplateCtr
from .code.system import NotATemplate
from .code.system_probe import ConfigItemRequiredError, FixtureProbeTemplate, SystemProbe


class SystemJob:

    def __init__(self, cfg_item_creg, system_config):
        self._cfg_item_creg = cfg_item_creg  # Used only from 'run' method, inside job process.
        self._system_config = system_config  # --//--

    def _configure_system(self, system, resource_list):
        for resource in resource_list:
            resource.configure_system(system)

    def _ctr_collector_config(self, resource_list):
        config = {}
        for resource in resource_list:
            for key, value in resource.ctr_collector_config().items():
                config.update({key: NotATemplate(value)})
        return config

    def _prepare_system(self, resources):
        system = SystemProbe()
        system.load_config(self._system_config)
        self._configure_system(system, resources)
        system.update_config('ctr_collector', self._ctr_collector_config(resources))
        _ = system.resolve_service('marker_registry')
        return system
        return ctr_collector

    def _enum_constructor_refs(self, system, ctr_collector):
        for name, rec in system.resolved_templates.items():
            log.info("Resolved service %s: %s", name, rec)
            ctr = ServiceTemplateCtr.from_rec(name, rec)
            yield mosaic.put(ctr.piece)
        for (service_name, t), rec in system.resolved_actors.items():
            log.info("Resolved actor %s.%s: %s", service_name, t, rec)
            ctr = ActorTemplateCtr.from_rec(service_name, t, rec)
            yield mosaic.put(ctr.piece)
        for ctr in ctr_collector.constructors:
            yield mosaic.put(ctr)
