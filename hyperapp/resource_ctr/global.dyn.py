import logging
import re

from . import htypes
from .htypes import attribute, partial, call, global_command, htest, impl, lcs
from .services import (
    mosaic,
    resource_type_producer,
    resource_module_factory,
    resource_module_registry,
    fixture_resource_module_registry,
    runner_method_collect_attributes_ref,
    runner_method_get_resource_type_ref,
    )

log = logging.getLogger(__name__)


name_to_module = {
    var_name: resource_module
    for resource_module_name, resource_module in resource_module_registry.items()
    for var_name in resource_module
    if not resource_module_name.startswith('legacy_type.')
    }

fixture_to_module = {
    var_name: resource_module
    for resource_module_name, resource_module in fixture_resource_module_registry.items()
    for var_name in resource_module
    if not resource_module_name.startswith('legacy_type.')
    }


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def construct_attr(resource_module, object_res_name, attr, add_object_prefix=True):
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


def construct_resource_params_partial(resource_module, fix_module, attr, attr_res_name):
    attr_snake_name = camel_to_snake(attr.name)
    param_to_resource = {}
    fix_param_to_resource = {}
    for idx, param_name in enumerate(attr.param_list):
        if param_name != 'piece':
            param_module = name_to_module[param_name]
            full_resource_name = f'{param_module.name}.{param_name}'
            param_to_resource[param_name] = full_resource_name
            resource_module.add_import(full_resource_name)
        try:
            fix_resource_name = f'{attr_snake_name}_{param_name}'
            param_module = fixture_to_module[fix_resource_name]
        except KeyError:
            fix_param_to_resource[param_name] = full_resource_name
            fix_module.add_import(full_resource_name)
        else:
            full_resource_name = f'{param_module.name}.{fix_resource_name}'
            fix_param_to_resource[param_name] = full_resource_name
            fix_module.add_import(full_resource_name)
    partial_res_name = f'{attr_snake_name}_partial'
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
    resource_module.set_definition(partial_res_name, partial_res_t, partial_def)
    if fix_param_to_resource:
        fix_partial_def = partial_def_t(
            function=attr_res_name,
            params=[
                partial_param_def_t(param_name, resource_name)
            for param_name, resource_name
                in fix_param_to_resource.items()
            ],
        )
        fix_module.set_definition(partial_res_name, partial_res_t, fix_partial_def)
    return partial_res_name


def construct_call(resource_module, function_res_name, res_name):
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
            return (name, name_to_type[name])
        except KeyError:
            pass
    raise RuntimeError(f"{object_name}: Unable to pick key element from: {list(name_to_type)}")


def construct_module_dir(module_name, resource_module, target_res_name):
    type_module_name = module_name.split('.')[-1]
    dir_t_res_name = f'legacy_type.{type_module_name}.{target_res_name}_d'
    return construct_dir(resource_module, target_res_name, dir_t_res_name)


def construct_dir(resource_module, target_res_name, dir_t_res_name):
    call_res_t = resource_type_producer(htypes.call.call)
    call_def = call_res_t.definition_t(
        function=dir_t_res_name,
        )
    res_name = f'{target_res_name}_d'
    resource_module.set_definition(res_name, call_res_t, call_def)
    resource_module.add_import(dir_t_res_name)
    return res_name


def construct_object_commands_dir(resource_module):
    dir_t_res_name = f'legacy_type.command.object_commands_d'
    return construct_dir(resource_module, 'object_commands', dir_t_res_name)


def construct_list_spec(module_name, resource_module, object_name, object_res_name, result_t):
    dir_res_name = construct_module_dir(module_name, resource_module, object_res_name)

    key_attribute, key_t_name = pick_key_t(object_name, result_t)
    key_t_res_name = f'legacy_type.{key_t_name.module}.{key_t_name.name}'
    resource_module.add_import(key_t_res_name)
    spec_res_t = resource_type_producer(htypes.impl.list_spec)
    spec_def = spec_res_t.definition_t(
        key_attribute=key_attribute,
        key_t=key_t_res_name,
        dir=dir_res_name,
        )
    res_name = f'{object_res_name}_spec'
    resource_module.set_definition(res_name, spec_res_t, spec_def)
    return (res_name, dir_res_name)


def construct_impl(
        module_name,
        get_resource_type_call,
        resource_module,
        fix_module,
        object_name,
        object_res_name,
        partial_res_name,
        get_attr,
        ):
    get_attr_res_name = construct_attr(fix_module, object_res_name, get_attr, add_object_prefix=True)

    get_call_res_name = f'{object_res_name}_{get_attr.name}_call'
    construct_call(fix_module, get_attr_res_name, get_call_res_name)
    get_call_res = resource_module.with_module(fix_module)[get_call_res_name]
    result_t = get_resource_type_call(mosaic.put(get_call_res))
    log.info("%s 'get' method result type: %r", object_res_name, result_t)

    if isinstance(result_t, htypes.htest.list_t):
        spec_res_name, dir_res_name = construct_list_spec(
            module_name, resource_module, object_name, object_res_name, result_t)
    else:
        raise RuntimeError(f"{resource_module.name}: Unknown {object_name}.{get_attr.name} method result type: {result_t!r}")

    fixture_name = f'{object_res_name}_piece'
    fixture_module = fixture_to_module[fixture_name]
    fixture_res = fixture_module[fixture_name]
    piece_t = get_resource_type_call(mosaic.put(fixture_res))
    log.info("%s piece type: %r", object_res_name, piece_t)
    if not isinstance(piece_t, htypes.htest.record_t):
        raise RuntimeError(f"{resource_module.name}: {object_res_name}: Expected record type, but got: {piece_t!r}")

    assoc_res_t = resource_type_producer(htypes.impl.impl_association)
    piece_t_name = f'legacy_type.{piece_t.type.module}.{piece_t.type.name}'
    assoc_def = assoc_res_t.definition_t(
        piece_t=piece_t_name,
        ctr_fn=partial_res_name,
        spec=spec_res_name,
        )
    resource_module.add_association(assoc_res_t, assoc_def)
    resource_module.add_import(piece_t_name)

    return dir_res_name


def construct_command(module_name, resource_module, object_res_name, object_dir_res_name, partial_res_name, attr):
    dir_res_name = construct_module_dir(module_name, resource_module, f'{object_res_name}_{attr.name}')

    command_res_t = resource_type_producer(htypes.impl.object_command_impl)
    command_def = command_res_t.definition_t(
        object_ctr=partial_res_name,
        method=attr.name,
        params=attr.param_list,
        dir=dir_res_name,
    )
    command_res_name = f'{object_res_name}_{attr.name}_command'
    resource_module.set_definition(command_res_name, command_res_t, command_def)

    # Called for every command, but results is single resource.
    object_commands_d_res_name = construct_object_commands_dir(resource_module)

    association_res_t = resource_type_producer(htypes.lcs.lcs_set_resource_association)
    association_def = association_res_t.definition_t(
        dir=(object_dir_res_name, object_commands_d_res_name),
        value=command_res_name,
        )
    resource_module.add_association(association_res_t, association_def)


def construct_global_command(module_name, resource_module, attr_res_name, function_res_name):
    dir_res_name = construct_module_dir(module_name, resource_module, attr_res_name)

    command_res_t = resource_type_producer(htypes.impl.global_command_impl)
    command_def = command_res_t.definition_t(
        function=function_res_name,
        dir=dir_res_name,
        )
    command_res_name = f'{attr_res_name}_command'
    resource_module.set_definition(command_res_name, command_res_t, command_def)

    association_res_t = resource_type_producer(htypes.global_command.global_command_association)
    association_def = association_res_t.definition_t(
        command=command_res_name,
        )
    resource_module.add_association(association_res_t, association_def)


def construct_global(root_dir, module_name, resource_module, process, module_res_name, globl):
    collect_attributes_call = process.rpc_call(runner_method_collect_attributes_ref)
    get_resource_type_call = process.rpc_call(runner_method_get_resource_type_ref)

    fix_module_name = f'{module_name}.with-fixtures'
    fix_module_rpath = module_name.replace('.', '/') + '.with-fixtures'
    fix_module = resource_module_factory(
        fix_module_name, root_dir / f'{fix_module_rpath}.resources.yaml', allow_missing=True)

    attr_res_name = construct_attr(resource_module, module_res_name, globl, add_object_prefix=False)
    partial_res_name = construct_resource_params_partial(
        resource_module, fix_module, globl, attr_res_name)
    object_res_name = camel_to_snake(globl.name)
    construct_call(fix_module, partial_res_name, object_res_name)

    object_res = resource_module.with_module(fix_module)[object_res_name]
    log.info("Object/service resource %s: %r", object_res_name, object_res)
    attr_list = collect_attributes_call(mosaic.put(object_res))
    log.info("Attributes for %s: %r", object_res_name, attr_list)

    name_to_attr = {
        attr.name: attr
        for attr in attr_list
        }

    if 'get' in name_to_attr and globl.param_list and globl.param_list[0] == 'piece':
        object_dir_res_name = construct_impl(
            module_name,
            get_resource_type_call,
            resource_module,
            fix_module,
            globl.name,
            object_res_name,
            partial_res_name,
            name_to_attr['get'],
            )
        for attr in attr_list:
            if attr.name == 'get':
                continue
            construct_command(module_name, resource_module, object_res_name, object_dir_res_name, partial_res_name, attr)
    else:
        construct_global_command(module_name, resource_module, object_res_name, partial_res_name)
