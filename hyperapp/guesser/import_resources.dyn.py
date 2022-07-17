from . import htypes
from .services import (
    builtin_services,
    local_modules,
    local_types,
    mosaic,
    resource_module_registry,
    )


def available_import_resources():
    # Types:
    for module_name, type_module in local_types.items():
        for name, type_ref in type_module.items():
            resource_ref = htypes.legacy_type.type(type_ref)
            yield (f'htypes.{module_name}.{name}', resource_ref)
    # Legacy builtin services:
    if service_name in builtin_services:
        resource = htypes.legacy_service.builtin_service(service_name)
        resource_ref = mosaic.put(resource)
        yield (f'services.{service_name}', resource_ref)
    # Legacy module services:
    for module_name, service_name_set in local_modules.module_provides.items():
        code_module = local_modules.by_name[module_name]
        for service_name in service_name_set:
            code_module_ref = mosaic.put(code_module)
            resource = htypes.legacy_service.module_service(service_name, code_module_ref)
            resource_ref = mosaic.put(resource)
            yield (f'services.{service_name}', resource_ref)
    # Resources as services:
    for module_name, res_module in resource_module_registry.items():
        for name in res_module:
            resource = res_module[name]
            resource_ref = mosaic.put(resource)
            yield (f'services.{name}', resource_ref)
    # Legacy modules:
    for full_name in local_modules.by_name:
        package_name, name = full_name.rsplit('.', 1)
        module_res = resource_module_registry[f'legacy_module.{package_name}']
        resource = module_res[name]
        resource_ref = mosaic.put(resource)
        yield (f'{name}', resource_ref)
