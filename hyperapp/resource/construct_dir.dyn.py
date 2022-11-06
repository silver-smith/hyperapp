from . import htypes
from .services import (
    resource_type_producer,
    types,
  )


def construct_dir(resource_module, dir_t, target_res_name):
    dir_res_t = resource_type_producer(dir_t)
    dir_def = dir_res_t.definition_t()
    resource_module.set_definition(target_res_name, dir_res_t, dir_def)
    # dir_t_res_name = f'legacy_type.{t.module_name}:{t.name}'
    # resource_module.add_import(dir_t_res_name)


def construct_module_dir(custom_types, resource_module, type_module_name, target_res_name):
    dir_t_ref = custom_types[type_module_name][target_res_name]
    dir_t = types.resolve(dir_t_ref)
    construct_dir(resource_module, dir_t, target_res_name)


def construct_object_commands_dir(resource_module):
    target_res_name = 'object_commands_d'
    construct_dir(resource_module, htypes.command.object_commands_d, target_res_name)
    return target_res_name
