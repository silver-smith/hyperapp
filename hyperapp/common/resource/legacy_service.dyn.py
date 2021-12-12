import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class LegacyServiceResource:

    def __init__(self, service_name, module_name, module_resource, services):
        self._service_name = service_name
        self._module_name = module_name  # Module providing this service.
        self._module_resource = module_resource
        self._services = services

    def __repr__(self):
        return f"<LegacyService: {self._service_name}@{self._module_name}>"

    def value(self):
        _ = self._module_resource.value()  # Ensure it is loaded.
        return getattr(self._services, self._service_name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._register_services(services.builtin_resource_by_name, services.legacy_module_resources, services.local_modules, services)

    def _register_services(self, builtin_resource_by_name, legacy_module_resources, local_modules, services):
        for module_name, service_name_set in local_modules.module_provides.items():
            for service_name in service_name_set:
                module_resource = legacy_module_resources[module_name]
                resource = LegacyServiceResource(service_name, module_name, module_resource, services)
                builtin_resource_by_name[service_name] = resource
                log.info("Legacy service resource %s: %s", service_name, resource)
