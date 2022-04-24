import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class LegacyServiceResourceModule:

    def __init__(self, name_to_piece):
        self._name_to_piece = name_to_piece

    @property
    def name(self):
        return 'legacy_service'

    def __contains__(self, var_name):
        return var_name in self._name_to_piece

    def __getitem__(self, var_name):
        return self._name_to_piece[var_name]

    def __iter__(self):
        return iter(self._name_to_piece)


def make_legacy_service_resource_module(mosaic, services, builtin_services, local_modules):
    name_to_piece = {}
    for service_name in builtin_services:
        piece = htypes.legacy_service.builtin_service(service_name)
        name_to_piece[service_name] = piece
        log.info("Builtin legacy service resource %r: %s", service_name, piece)
    for module_name, service_name_set in local_modules.module_provides.items():
        for service_name in service_name_set:
            code_module = local_modules.by_name[module_name]
            code_module_ref = mosaic.put(code_module)
            piece = htypes.legacy_service.module_service(service_name, code_module_ref)
            name_to_piece[service_name] = piece
            log.info("Legacy service resource %r: %s", service_name, piece)
    return LegacyServiceResourceModule(name_to_piece)


def builtin_service_python_object(piece, services):
    return getattr(services, piece.name)


def module_service_python_object(piece, python_object_creg, services):
    _ = python_object_creg.invite(piece.module_ref)  # Ensure it is loaded.
    return getattr(services, piece.name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_module_registry['legacy_service'] = make_legacy_service_resource_module(
            services.mosaic, services, services.builtin_services, services.local_modules)

        services.python_object_creg.register_actor(htypes.legacy_service.builtin_service, builtin_service_python_object, services)
        services.python_object_creg.register_actor(htypes.legacy_service.module_service, module_service_python_object, services.python_object_creg, services)
