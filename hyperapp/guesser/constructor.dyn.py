from . import htypes
from .services import (
    resource_module_factory,
    resource_type_producer,
    )


def pick_key_t(error_prefix, result_t):
    name_to_type = {
        element.name: element.type
        for element in result_t.element_list
        }
    for name in ['id', 'key', 'name']:
        try:
            return (name, name_to_type[name])
        except KeyError:
            pass
    raise RuntimeError(f"{error_prefix}: Unable to pick key element from: {list(name_to_type)}")


class Constructor:

    def __init__(self, resource_module_reg, import_resources, root_dir, full_module_name, module_name, module_path):
        self._module_name = module_name
        self.resource_module = resource_module_factory(
            resource_module_registry=resource_module_reg,
            name=full_module_name,
            path=module_path.with_name(f'{module_path.name}_auto_import.resources.yaml'),
            load_from_file=False,
            )
        self._import_to_res_name = {
            import_name: rec.resource_name
            for import_name, rec in import_resources.items()
            }
        self._module_res_name = module_name.replace('.', '_') + '.module'

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

    def on_global(self, process, attr, result_t, ctx):
        global_res_name = attr.resource_name or attr.name
        self._construct_attr(global_res_name, self._module_res_name, attr)
        # if isinstance(attr, htypes.inspect.fn_attr):
        #     self._construct_service(self._module_res_name, global_res_name)
        return global_res_name

    def on_attr(self, process, attr, result_t, global_res_name):
        if attr.name != 'get':
            return
        if isinstance(result_t, htypes.inspect.list_t):
            self._construct_list_spec(global_res_name, result_t)
        else:
            raise RuntimeError(f"{self.resource_module.name}: Unsupported {global_res_name}.{attr.name} method result type: {result_t!r}")

    def _construct_list_spec(self, global_res_name, result_t):
        dir_res_name = self._construct_module_dir(target_res_name=global_res_name)

    def _construct_module_dir(self, target_res_name):
        type_module_name = self._module_name
        dir_t_res_name = f'legacy_type.{type_module_name}.{target_res_name}_d'
        return self._construct_dir(target_res_name, dir_t_res_name)

    def _construct_dir(self, target_res_name, dir_t_res_name):
        call_res_t = resource_type_producer(htypes.call.call)
        call_def = call_res_t.definition_t(
            function=dir_t_res_name,
            )
        res_name = f'{target_res_name}_d'
        self.resource_module.set_definition(res_name, call_res_t, call_def)
        self.resource_module.add_import(dir_t_res_name)
        return res_name

    def _construct_attr(self, target_name, object_res_name, attr):
        attr_res_t = resource_type_producer(htypes.attribute.attribute)
        attr_def = attr_res_t.definition_t(
            object=object_res_name,
            attr_name=attr.name,
            )
        self.resource_module.set_definition(target_name, attr_res_t, attr_def)

    def _construct_service(self, module_res_name, attr_name):
        target_name = f'{attr_name}.service'
        call_res_t = resource_type_producer(htypes.call.call)
        call_def = call_res_t.definition_t(
            function=attr_name,
            )
        self.resource_module.set_definition(target_name, call_res_t, call_def)
