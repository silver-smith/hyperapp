from hyperapp.resource.legacy_type import add_legacy_types_to_cache

from .services import (
    builtin_service_resource_loader,
    legacy_type_resource_loader,
    resource_registry_factory,
    type_module_loader,
    )


def create_custom_resource_registry(build):
    res_reg = resource_registry_factory()
    legacy_type_modules = legacy_type_resource_loader(build.types.as_dict)
    add_legacy_types_to_cache(res_reg, legacy_type_modules)
    res_reg.update_modules(legacy_type_modules)
    res_reg.set_module('builtins', builtin_service_resource_loader(res_reg))
    return res_reg
