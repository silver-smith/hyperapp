from collections import namedtuple

from .services import (
    code_module_loader,
    legacy_module_resource_loader,
    legacy_type_resource_loader,
    local_modules,
    local_types,
    resource_loader,
    resource_module_registry,
    type_module_loader,
    )


CustomResources = namedtuple('CustomResources', 'types modules res_module_reg')


def load_custom_resources(resources_dir):
    custom_types = {**local_types}
    type_module_loader.load_type_modules([resources_dir.root], custom_types)
    custom_modules = local_modules.copy()
    code_module_loader.load_code_modules(custom_types, [resources_dir.root], custom_modules)
    module_reg = {
        **resource_module_registry,
        **legacy_type_resource_loader(custom_types),
        **legacy_module_resource_loader(custom_modules),
        }
    resource_loader(resources_dir, module_reg)
    return CustomResources(
        types=custom_types,
        modules=custom_modules,
        res_module_reg=module_reg,
        )
