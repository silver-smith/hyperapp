import re

from . import htypes
from .services import (
    code_module_loader,
    legacy_module_resource_loader,
    legacy_type_resource_loader,
    local_modules,
    local_types,
    resource_loader,
    resource_module_factory,
    resource_module_registry,
    resource_type_producer,
    type_module_loader,
    )



def custom_res_module_reg(resources_dir):
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


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class Constructor:

    def __init__(self, root_dir, full_module_name, module_name, module_path):
        self._local_res_module_reg = custom_res_module_reg(module_path.parent)
        self.resource_module = resource_module_factory(
            resource_module_registry=self._local_res_module_reg,
            name=full_module_name,
            path=module_path.with_name(f'{module_path.name}_auto_import.resources.yaml'),
            load_from_file=False,
            )
        self._module_res_name = module_name.replace('.', '_') + '_module'

    def on_module(self, module_name, module_path, imports):
        module_res_t = resource_type_producer(htypes.python_module.python_module)
        import_rec_def_t = module_res_t.definition_t.fields['import_list'].element_t
        for r in imports:
            if '.' in r.resource_name:
                self.resource_module.add_import(r.resource_name)
        module_def = module_res_t.definition_t(
            module_name=module_name,
            file_name=module_path.name,
            import_list=[
                import_rec_def_t(r.name, r.resource_name)
                for r in imports
                ],
            )
        self.resource_module.set_definition(self._module_res_name, module_res_t, module_def)

    def on_global(self, process, attr):
        attr_snake_name = camel_to_snake(attr.name)
        target_name = attr.resource_name or f'{attr_snake_name}_attribute'
        self._construct_attr(target_name, self._module_res_name, attr)

    def _construct_attr(self, target_name, object_res_name, attr):
        attr_res_t = resource_type_producer(htypes.attribute.attribute)
        attr_def = attr_res_t.definition_t(
            object=object_res_name,
            attr_name=attr.name,
            )
        self.resource_module.set_definition(target_name, attr_res_t, attr_def)
