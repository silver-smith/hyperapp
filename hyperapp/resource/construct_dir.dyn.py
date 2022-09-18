from . import htypes
from .services import (
    resource_type_producer,
  )


def construct_dir(resource_module, target_res_name, dir_t_res_name):
    call_res_t = resource_type_producer(htypes.call.call)
    call_def = call_res_t.definition_t(
        function=dir_t_res_name,
        )
    resource_module.set_definition(target_res_name, call_res_t, call_def)
    resource_module.add_import(dir_t_res_name)


def construct_module_dir(resource_module, type_module_name, target_res_name):
    dir_t_res_name = f'legacy_type.{type_module_name}:{target_res_name}'
    construct_dir(resource_module, target_res_name, dir_t_res_name)


def construct_object_commands_dir(resource_module):
    target_res_name = 'object_commands_d'
    dir_t_res_name = f'legacy_type.command:object_commands_d'
    construct_dir(resource_module, target_res_name, dir_t_res_name)
    return target_res_name
