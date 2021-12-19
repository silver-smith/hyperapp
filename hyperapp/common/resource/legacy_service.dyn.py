import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


def builtin_service_python_object(piece, services):
    return getattr(services, piece.name)


def module_service_python_object(piece, python_object_creg, services):
    _ = python_object_creg.invite(piece.module_ref)  # Ensure it is loaded.
    return getattr(services, piece.name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._register_services(
            services.mosaic, services, services.builtin_services, services.builtin_resource_by_name, services.local_modules)
        services.python_object_creg.register_actor(htypes.legacy_service.builtin_service, builtin_service_python_object, services)
        services.python_object_creg.register_actor(htypes.legacy_service.module_service, module_service_python_object, services.python_object_creg, services)

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
