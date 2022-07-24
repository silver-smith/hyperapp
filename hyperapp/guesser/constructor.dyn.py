from . import htypes
from .services import (
    resource_module_factory,
    resource_type_producer,
    )


class Constructor:

    def __init__(self, resource_module_reg, import_resources, root_dir, full_module_name, module_name, module_path):
        self.resource_module = resource_module_factory(
            resource_module_registry=resource_module_reg,
            name=full_module_name,
            path=module_path.with_name(f'{module_path.name}_auto_import.resources.yaml'),
            load_from_file=False,
            )
        self._import_to_res_name = {
            rec.import_name: rec.resource_name
            for rec in import_resources
            }
        self._module_res_name = module_name.replace('.', '_') + '_module'

    def on_module(self, module_name, module_path, imports):
        module_res_t = resource_type_producer(htypes.python_module.python_module)
        import_rec_def_t = module_res_t.definition_t.fields['import_list'].element_t
        import_list = []
        for name in imports:
            resource_name = self._import_to_res_name[name]
            self.resource_module.add_import(resource_name)
            import_list.append(import_rec_def_t(name, resource_name))
        module_def = module_res_t.definition_t(
            module_name=module_name,
            file_name=module_path.name,
            import_list=import_list,
            )
        self.resource_module.set_definition(self._module_res_name, module_res_t, module_def)

    def on_global(self, process, attr, result_t):
        target_name = attr.resource_name or attr.name
        self._construct_attr(target_name, self._module_res_name, attr)

    def on_attr(self, process, attr, result_t):
        pass

    def _construct_attr(self, target_name, object_res_name, attr):
        attr_res_t = resource_type_producer(htypes.attribute.attribute)
        attr_def = attr_res_t.definition_t(
            object=object_res_name,
            attr_name=attr.name,
            )
        self.resource_module.set_definition(target_name, attr_res_t, attr_def)
