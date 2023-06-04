import logging
from collections import defaultdict
from functools import partial

from hyperapp.common.htypes.legacy_service import legacy_service_t
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class LegacyServiceResourceModule:

    def __init__(self, name_to_piece):
        self._name_to_piece = name_to_piece

    @property
    def name(self):
        return 'legacy_service'

    def __setitem__(self, name, service_piece):
        self._name_to_piece[name] = service_piece

    def __contains__(self, var_name):
        return var_name in self._name_to_piece

    def __getitem__(self, var_name):
        return self._name_to_piece[var_name]

    def __iter__(self):
        return iter(self._name_to_piece)

    @property
    def associations(self):
        return set()

    def merge_with(self, other):
        assert isinstance(other, LegacyServiceResourceModule)
        return LegacyServiceResourceModule({
            **self._name_to_piece,
            **other._name_to_piece,
            })


def make_legacy_service_resource_module(mosaic, services, module_registry, builtin_services, resource_registry, local_modules):
    name_to_piece = {}

    for service_name in builtin_services:
        piece = legacy_service_t(service_name)
        name_to_piece[service_name] = piece
        log.info("Builtin legacy service resource %r: %s", service_name, piece)

    loaded_modules = {
        rec.name for rec in module_registry.elements()
        }
    service_provider = defaultdict(list)
    for module_name, service_name_set in local_modules.module_provides.items():
        for service_name in service_name_set:
            service_provider[service_name].append(module_name)
    for service_name, module_name_list in service_provider.items():
        if len(module_name_list) > 1:
            for module_name in module_name_list:
                if module_name in loaded_modules:
                    break
            else:
                raise RuntimeError(f"Several modules provide {service_name!r}, but no one is loaded: {module_name_list}")
        else:
            [module_name] = module_name_list
        code_module = local_modules.by_name[module_name]
        code_module_ref = mosaic.put(code_module)
        piece = htypes.legacy_service.module_service(service_name, code_module_ref)
        name_to_piece[service_name] = piece
        log.info("Legacy service resource %r: %s", service_name, piece)

    for name, piece in name_to_piece.items():
        resource_registry.add_to_cache(('legacy_service', name), piece)
    return LegacyServiceResourceModule(name_to_piece)


def builtin_service_python_object(piece, services):
    return getattr(services, piece.name)


def module_service_python_object(piece, python_object_creg, services):
    _ = python_object_creg.invite(piece.module_ref)  # Ensure it is loaded.
    try:
        return getattr(services, piece.name)
    except AttributeError as x:
        # Allowing AttributeError leaving __getattr__ leads to undesired behaviour when called from import statement.
        raise RuntimeError(f"Error retrieving service {piece.name!r}: {x}")


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.legacy_service_resource_loader = loader = partial(
            make_legacy_service_resource_module, services.mosaic, services, services.module_registry, services.builtin_services)
        services.resource_registry.set_module('legacy_service', loader(services.resource_registry, services.local_modules))

        services.python_object_creg.register_actor(legacy_service_t, builtin_service_python_object, services)
        services.python_object_creg.register_actor(htypes.legacy_service.module_service, module_service_python_object, services.python_object_creg, services)
