import re
from collections import defaultdict, namedtuple

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


def override_import_resources_with_fixtures(import_resources, fixtures_module=None):
    if not fixtures_module:
        return import_resources
    overridden_resources = import_resources.copy()
    modules = defaultdict(dict)  # module -> attr name -> resource ref
    for name in fixtures_module:
        if name.startswith('module.'):
            try:
                _, module_name, attr_name = name.split('.')
            except ValueError:
                raise RuntimeError(f"Module override should be in the form 'module.<module-name>.<attr-name>': {name!r}")
            modules[module_name][attr_name] = mosaic.put(fixtures_module[name])
    for module_name, attributes in modules.items():
        try:
            original_import_res = import_resources[module_name]
        except KeyError:
            raise RuntimeError(f"Attempt to override non-existing module {module_name!r}: {', '.join(attrs)}")
        attr_list = [
            htypes.mock_module.attribute(name, ref)
            for name, ref in attributes.items()
            ]
        resource = htypes.mock_module.mock_module(attr_list)
        overridden_resources[module_name] = ImportRes(mosaic.put(resource), original_import_res.resource_name)
    return overridden_resources
