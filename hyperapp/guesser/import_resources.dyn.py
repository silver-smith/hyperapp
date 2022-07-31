import re
from collections import namedtuple

from . import htypes
from .services import (
    builtin_services,
    mosaic,
    )


ImportRes = namedtuple('ImportResource', 'resource_ref resource_name')


def available_import_resources(custom_resources):
    # Types:
    for module_name, type_module in custom_resources.types.items():
        for name, type_ref in type_module.items():
            resource = htypes.legacy_type.type(type_ref)
            resource_ref = mosaic.put(resource)
            yield (f'htypes.{module_name}.{name}', ImportRes(resource_ref, f'legacy_type.{module_name}:{name}'))
    # Legacy builtin services:
    for service_name in builtin_services:
        resource = htypes.legacy_service.builtin_service(service_name)
        resource_ref = mosaic.put(resource)
        yield (f'services.{service_name}', ImportRes(resource_ref, f'legacy_service:{service_name}'))
    # Legacy module services:
    for module_name, service_name_set in custom_resources.modules.module_provides.items():
        code_module = custom_resources.modules.by_name[module_name]
        for service_name in service_name_set:
            code_module_ref = mosaic.put(code_module)
            resource = htypes.legacy_service.module_service(service_name, code_module_ref)
            resource_ref = mosaic.put(resource)
            yield (f'services.{service_name}', ImportRes(resource_ref, f'legacy_service:{service_name}'))
    # Resources as services and modules:
    for module_name, res_module in custom_resources.res_module_reg.items():
        if module_name.startswith(('legacy_type.', 'legacy_service.', 'legacy_module.')):
            continue
        for name in res_module:
            mo = re.match(r'(.+)\.module$', name)
            if mo:
                import_module_name = mo[1]
                resource = res_module[name]
                resource_ref = mosaic.put(resource)
                yield (import_module_name, ImportRes(resource_ref, f'{module_name}:{name}'))
                continue
            mo = re.match(r'(.+)\.service$', name)
            if mo:
                service_name = mo[1]
                resource = res_module[name]
                resource_ref = mosaic.put(resource)
                yield (f'services.{service_name}', ImportRes(resource_ref, f'{module_name}:{name}'))
                continue
    # Legacy modules:
    for full_name in custom_resources.modules.by_name:
        package_name, name = full_name.rsplit('.', 1)
        module_res = custom_resources.res_module_reg[f'legacy_module.{package_name}']
        resource = module_res[name]
        resource_ref = mosaic.put(resource)
        yield (name, ImportRes(resource_ref, f'legacy_module.{package_name}:{name}'))
