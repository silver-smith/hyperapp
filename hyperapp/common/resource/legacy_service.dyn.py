import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class LegacyServiceResource:

    def __init__(self, service_name, module_name, services):
        self._service_name = service_name
        self._module_name = module_name  # Module providing this service.
        self._services = services

    def __repr__(self):
        return f"<LegacyService: {self._service_name}@{self._module_name}>"


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._register_services(services, services.builtin_resource_by_name, services.local_modules, services.module_registry)

    def _register_services(self, services, builtin_resource_by_name, local_modules, module_registry):
        for module_name, service_name_set in local_modules.module_provides.items():
            for service_name in service_name_set:
                resource = LegacyServiceResource(service_name, module_name, services)
                builtin_resource_by_name[service_name] = resource
                log.info("Legacy service resource %s: %s", service_name, resource)
