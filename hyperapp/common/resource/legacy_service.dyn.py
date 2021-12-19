import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class BuiltinLegacyServiceResource:

    def __init__(self, service_name, services):
        self._service_name = service_name
        self._services = services

    def __repr__(self):
        return f"<BuiltinLegacyService: {self._service_name}>"

    def value(self):
        return getattr(self._services, self._service_name)


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

        self._register_services(
            services.mosaic, services, services.builtin_services, services.builtin_resource_by_name, services.local_modules)

    def _register_services(self, mosaic, services, builtin_services, builtin_resource_by_name, local_modules):
        for service_name in builtin_services:
            piece = htypes.legacy_service.builtin_service(service_name)
            builtin_resource_by_name[service_name] = mosaic.put(piece)
            log.info("Builtin legacy service resource %s: %s", service_name, piece)
        for module_name, service_name_set in local_modules.module_provides.items():
            for service_name in service_name_set:
                module_ref = builtin_resource_by_name[module_name]
                piece = htypes.legacy_service.module_service(service_name, module_ref)
                builtin_resource_by_name[service_name] = mosaic.put(piece)
                log.info("Legacy service resource %s: %s", service_name, piece)
