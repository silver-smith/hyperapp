import logging
import re

from . import htypes

log = logging.getLogger(__name__)


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def construct_attr(resource_type_reg, resource_module, object_res_name, attr, add_object_prefix=True):
    attr_res_t = resource_type_reg[htypes.attribute.attribute]
    attr_def = attr_res_t.definition_t(
        object=object_res_name,
        attr_name=attr.name,
        )
    attr_snake_name = camel_to_snake(attr.name)
    attr_res_name = f'{attr_snake_name}_attribute'
    if add_object_prefix:
        attr_res_name = f'{object_res_name}_{attr_res_name}'
    resource_module.set_definition(attr_res_name, attr_res_t, attr_def)
    return attr_res_name


def construct_resource_params_partial(resource_type_reg, resource_module_registry, resource_module, attr, attr_res_name):
    name_to_module = {
        var_name: resource_module_name
        for resource_module_name, resource_module in resource_module_registry.items()
        for var_name in resource_module
        }
    param_to_resource = {}
    for param_name in attr.param_list:
        resource_module_name = name_to_module[param_name]
        resource_name = f'{resource_module_name}.{param_name}'
        param_to_resource[param_name] = resource_name
        resource_module.add_import(resource_name)
    partial_res_t = resource_type_reg['partial']
    partial_def_t = partial_res_t.definition_t
    partial_param_def_t = partial_def_t.fields['params'].element_t
    partial_def = partial_def_t(
        function=attr_res_name,
        params=[
            partial_param_def_t(param_name, resource_name)
            for param_name, resource_name
            in param_to_resource.items()
            ],
        )
    partial_res_name = f'{attr_res_name}_partial'
    resource_module.set_definition(partial_res_name, partial_res_t, partial_def)
    return partial_res_name


def construct_call(resource_type_reg, resource_module, function_res_name, res_name):
    call_res_t = resource_type_reg['call']
    call_def = call_res_t.definition_t(
        function=function_res_name,
        )
    resource_module.set_definition(res_name, call_res_t, call_def)


def construct_global(
        module_name, resource_module, process, module_res_name, name_to_module, globl,
        mosaic, resource_type_reg, resource_module_registry, runner_method_collect_attributes_ref,
        ):
    collect_attributes_call = process.rpc_call(runner_method_collect_attributes_ref)

    attr_res_name = construct_attr(resource_type_reg, resource_module, module_res_name, globl, add_object_prefix=False)
    partial_res_name = construct_resource_params_partial(resource_type_reg, resource_module_registry, resource_module, globl, attr_res_name)
    global_res_name = camel_to_snake(globl.name)
    construct_call(resource_type_reg, resource_module, partial_res_name, global_res_name)

    global_res = resource_module[global_res_name]
    log.info("Function resource %s: %r", global_res_name, global_res)
    attr_list = collect_attributes_call(mosaic.put(global_res))
    log.info("Attributes for %s: %r", global_res_name, attr_list)

    # for attr in attr_list:
    #     if 'current_key' in attr.param_list:
    #         self._process_command(resource_module, global_snake_name, attr, state_attributes=['current_key'])
    #     if attr.param_list in {(), ('request',)}:
    #         self._process_service(module_name, resource_module, process, global_snake_name, object_res, attr)
