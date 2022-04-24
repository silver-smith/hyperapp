import logging
import re

from . import htypes

log = logging.getLogger(__name__)


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def construct_attr(resource_type_producer, resource_module, object_res_name, attr, add_object_prefix=True):
    attr_res_t = resource_type_producer(htypes.attribute.attribute)
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


def construct_resource_params_partial(
        resource_type_producer, resource_module_registry, fixture_resource_module_registry, resource_module, attr, attr_res_name):
    name_to_module = {
        var_name: resource_module_name
        for resource_module_name, resource_module in resource_module_registry.items()
        for var_name in resource_module
        }
    fixture_to_module = {
        var_name: f'{resource_module_name}.fixtures'
        for resource_module_name, resource_module in fixture_resource_module_registry.items()
        for var_name in resource_module
        }
    attr_snake_name = camel_to_snake(attr.name)
    param_to_resource = {}
    for idx, param_name in enumerate(attr.param_list):
        try:
            resource_name = f'{attr_snake_name}_{param_name}'
            resource_module_name = fixture_to_module[resource_name]
        except KeyError:
            resource_name = param_name
            resource_module_name = name_to_module[resource_name]
        full_resource_name = f'{resource_module_name}.{resource_name}'
        param_to_resource[param_name] = full_resource_name
        resource_module.add_import(full_resource_name)
    partial_res_t = resource_type_producer(htypes.partial.partial)
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
    partial_res_name = f'{attr_snake_name}_partial'
    resource_module.set_definition(partial_res_name, partial_res_t, partial_def)
    return partial_res_name


def construct_call(resource_type_producer, resource_module, function_res_name, res_name):
    call_res_t = resource_type_producer(htypes.call.call)
    call_def = call_res_t.definition_t(
        function=function_res_name,
        )
    resource_module.set_definition(res_name, call_res_t, call_def)


def pick_key_t(object_name, result_t):
    name_to_type = {
        element.name: element.type
        for element in result_t.element_list
        }
    for name in ['id', 'key', 'name']:
        try:
            return name_to_type[name]
        except KeyError:
            pass
    raise RuntimeError(f"{object_name}: Unable to pick key element from: {list(name_to_type)}")


def construct_list_impl(resource_type_producer, resource_module, object_name, object_res_name, partial_res_name, result_t):
    key_t_name = pick_key_t(object_name, result_t)
    key_t_res_name = f'legacy_type.{key_t_name.module}.{key_t_name.name}'
    resource_module.add_import(key_t_res_name)
    impl_res_t = resource_type_producer(htypes.impl.list_impl)
    impl_def = impl_res_t.definition_t(
        function=partial_res_name,
        key_t=key_t_res_name,
        )
    res_name = f'{object_res_name}_impl'
    resource_module.set_definition(res_name, impl_res_t, impl_def)


def construct_impl(mosaic, resource_type_producer, resource_module, get_fn_result_t_call,
                   object_name, object_res_name, partial_res_name, get_attr):
    attr_res_name = construct_attr(resource_type_producer, resource_module, object_res_name, get_attr, add_object_prefix=True)
    attr_res = resource_module[attr_res_name]
    result_t = get_fn_result_t_call(mosaic.put(attr_res))
    log.info("%s 'get' method result type: %r", object_res_name, result_t)
    if isinstance(result_t, htypes.htest.list_t):
        construct_list_impl(resource_type_producer, resource_module, object_name, object_res_name, partial_res_name, result_t)


def construct_global(
        module_name, resource_module, process, module_res_name, globl,
        mosaic, resource_type_producer, resource_module_registry, fixture_resource_module_registry,
        runner_method_collect_attributes_ref,
        runner_method_get_function_result_type_ref,
        ):
    collect_attributes_call = process.rpc_call(runner_method_collect_attributes_ref)
    get_fn_result_t_call = process.rpc_call(runner_method_get_function_result_type_ref)

    attr_res_name = construct_attr(resource_type_producer, resource_module, module_res_name, globl, add_object_prefix=False)
    partial_res_name = construct_resource_params_partial(
        resource_type_producer, resource_module_registry, fixture_resource_module_registry, resource_module, globl, attr_res_name)
    object_res_name = camel_to_snake(globl.name)
    construct_call(resource_type_producer, resource_module, partial_res_name, object_res_name)

    object_res = resource_module[object_res_name]
    log.info("Object/service resource %s: %r", object_res_name, object_res)
    attr_list = collect_attributes_call(mosaic.put(object_res))
    log.info("Attributes for %s: %r", object_res_name, attr_list)

    name_to_attr = {
        attr.name: attr
        for attr in attr_list
    }
    if 'get' in name_to_attr:
        construct_impl(mosaic, resource_type_producer, resource_module, get_fn_result_t_call,
                       globl.name, object_res_name, partial_res_name, name_to_attr['get'])
