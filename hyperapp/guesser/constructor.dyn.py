import re
from collections import namedtuple

from . import htypes
from .services import (
    mosaic,
    resource_module_factory,
    resource_type_producer,
    constructor_creg,
    get_resource_type_ref,
    )


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def pick_key_t(result_t, error_prefix):
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


GlobalContext = namedtuple('GlobalContext', 'global_res_name global_dir_res_name global_attr')


class Constructor:

    def __init__(self, resource_module_reg, fixtures_module, import_resources, root_dir, full_module_name, module_name, module_path):
        self._fix_module = fixtures_module
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
        for ctr_ref in attr.constructors:
            self._run_constructor(attr, ctr_ref)
        # if isinstance(attr, htypes.inspect.fn_attr):
        #     if isinstance(result_t, htypes.inspect.record_t):
        #         if attr.param_list:
        #             self._construct_object_command(global_res_name, attr)
        #         else:
        #             self._construct_global_command(global_res_name)
            #     self._construct_service(self._module_res_name, global_res_name)
        global_dir_res_name = camel_to_snake(global_res_name) + '_d'
        return GlobalContext(global_res_name, global_dir_res_name, attr)

    def on_attr(self, process, attr, result_t, ctx):
        if not isinstance(attr, htypes.inspect.fn_attr):
            return
        if not isinstance(ctx.global_attr, htypes.inspect.fn_attr) or list(ctx.global_attr.param_list) != ['piece']:
            return
        if attr.name == 'get':
            self._construct_impl(process, ctx.global_res_name, ctx.global_dir_res_name, ctx.global_attr, attr, result_t)
        else:
            self._construct_method_command(ctx.global_res_name, ctx.global_dir_res_name, attr)

    def _construct_impl(self, process, global_res_name, global_dir_res_name, global_attr, attr, result_t):
        if isinstance(result_t, htypes.inspect.list_t):
            spec_res_name = self._construct_list_spec(global_res_name, global_dir_res_name, result_t)
        else:
            raise RuntimeError(
                f"{self.resource_module.name}: Unsupported {global_res_name}.{attr.name} method result type: {result_t!r}")

        piece_t_name = self._get_and_check_piece_param_res(process, global_res_name, global_attr)
        self.resource_module.add_import(piece_t_name)

        assoc_res_t = resource_type_producer(htypes.impl.impl_association)
        assoc_def = assoc_res_t.definition_t(
            piece_t=piece_t_name,
            ctr_fn=global_res_name,
            spec=spec_res_name,
            )
        self.resource_module.add_association(assoc_res_t, assoc_def)

        pyobject_a_res_t = resource_type_producer(htypes.impl.python_object_association)
        pyobject_a_def = pyobject_a_res_t.definition_t(
            t=piece_t_name,
            function=global_res_name,
            )
        self.resource_module.add_association(pyobject_a_res_t, pyobject_a_def)

    def _get_and_check_piece_param_res(self, process, global_res_name, global_attr):
        assert isinstance(global_attr, htypes.inspect.fn_attr)  # How can we get here if global is not a function?
        if list(global_attr.param_list) != ['piece']:
            raise RuntimeError(
                "Single parameter, 'piece', is expected for implementation object constructors,"
                f" but got: {global_attr.param_list!r}")
        piece_t = self._get_piece_param_t(process, global_res_name)
        if not isinstance(piece_t, htypes.inspect.record_t):
            raise RuntimeError(
                f"{self.resource_module.name}: {global_res_name} 'piece' parameter: Expected record type, but got: {piece_t!r}")
        return f'legacy_type.{piece_t.type.module}:{piece_t.type.name}'

    def _get_piece_param_t(self, process, global_res_name):
        get_resource_type = process.rpc_call(get_resource_type_ref)

        res_name = f'param.{global_res_name}.piece'
        resource = self._fix_module[res_name]
        resource_ref = mosaic.put(resource)
        return get_resource_type(resource_ref)

    def _construct_list_spec(self, global_res_name, global_dir_res_name, result_t):
        self._construct_module_dir(global_dir_res_name)

        key_attribute, key_t_name = pick_key_t(result_t, error_prefix=global_res_name)
        key_t_res_name = f'legacy_type.{key_t_name.module}:{key_t_name.name}'
        self.resource_module.add_import(key_t_res_name)
        spec_res_t = resource_type_producer(htypes.impl.list_spec)
        spec_def = spec_res_t.definition_t(
            key_attribute=key_attribute,
            key_t=key_t_res_name,
            dir=global_dir_res_name,
            )
        res_name = camel_to_snake(global_res_name) + '_spec'
        self.resource_module.set_definition(res_name, spec_res_t, spec_def)
        return res_name

    def _construct_object_command(self, global_res_name, global_attr):
        dir_res_name = camel_to_snake(global_res_name) + '_d'
        self._construct_module_dir(dir_res_name)

        command_res_t = resource_type_producer(htypes.impl.object_command_impl)
        command_def = command_res_t.definition_t(
            function=global_res_name,
            params=global_attr.param_list,
            dir=dir_res_name,
        )
        command_res_name = f'{global_res_name}.command'
        self.resource_module.set_definition(command_res_name, command_res_t, command_def)

        # todo: move following to separate method, decorate target function with destination dir.

        # Called for every command, but results is single resource.
        object_commands_d_res_name = self._construct_object_commands_dir()

        association_res_t = resource_type_producer(htypes.lcs.lcs_set_resource_association)
        association_def = association_res_t.definition_t(
            dir=(object_commands_d_res_name,),
            value=command_res_name,
            )
        self.resource_module.add_association(association_res_t, association_def)

    def _construct_method_command(self, global_res_name, global_dir_res_name, attr):
        global_snake_name = camel_to_snake(global_res_name)
        dir_res_name = f'{global_snake_name}_{attr.name}_d'
        self._construct_module_dir(dir_res_name)

        command_res_t = resource_type_producer(htypes.impl.method_command_impl)
        command_def = command_res_t.definition_t(
            method=attr.name,
            params=attr.param_list,
            dir=dir_res_name,
        )
        command_res_name = f'{global_snake_name}.{attr.name}.command'
        self.resource_module.set_definition(command_res_name, command_res_t, command_def)

        # Called for every command, but results is single resource.
        object_commands_d_res_name = self._construct_object_commands_dir()

        association_res_t = resource_type_producer(htypes.lcs.lcs_set_resource_association)
        association_def = association_res_t.definition_t(
            dir=(global_dir_res_name, object_commands_d_res_name),
            value=command_res_name,
            )
        self.resource_module.add_association(association_res_t, association_def)

    def _run_constructor(self, attr, ctr_ref):
        constructor_creg.invite(ctr_ref, self.resource_module, self._module_name, attr)

    def _construct_object_commands_dir(self):
        target_res_name = 'object_commands_d'
        dir_t_res_name = f'legacy_type.command:object_commands_d'
        self._construct_dir(target_res_name, dir_t_res_name)
        return target_res_name

    def _construct_module_dir(self, target_res_name):
        type_module_name = self._module_name
        dir_t_res_name = f'legacy_type.{type_module_name}:{target_res_name}'
        self._construct_dir(target_res_name, dir_t_res_name)

    def _construct_dir(self, target_res_name, dir_t_res_name):
        call_res_t = resource_type_producer(htypes.call.call)
        call_def = call_res_t.definition_t(
            function=dir_t_res_name,
            )
        self.resource_module.set_definition(target_res_name, call_res_t, call_def)
        self.resource_module.add_import(dir_t_res_name)

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
