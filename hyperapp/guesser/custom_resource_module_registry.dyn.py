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


def custom_resource_module_registry(resources_dir):
    custom_types = {**local_types}
    type_module_loader.load_type_modules([resources_dir], custom_types)
    custom_modules = local_modules.copy()
    code_module_loader.load_code_modules(custom_types, [resources_dir], custom_modules)
    module_reg = {
        **resource_module_registry,
        **legacy_type_resource_loader(custom_types),
        **legacy_module_resource_loader(custom_modules),
        }
    resource_loader([resources_dir], module_reg)
    return module_reg
