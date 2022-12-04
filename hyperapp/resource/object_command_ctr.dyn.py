import inspect
import re

from . import htypes
from .services import (
    mosaic,
    resource_type_producer,
  )
from .constants import RESOURCE_CTR_ATTR
from .construct_dir import construct_module_dir, construct_object_commands_dir


def object_command(fn):
    module = inspect.getmodule(fn)
    ctr_dict = module.__dict__.setdefault(RESOURCE_CTR_ATTR, {})
    ctr_list = ctr_dict.setdefault(fn.__name__, [])
    ctr = htypes.object_command_ctr.object_command_ctr()
    ctr_list.append(mosaic.put(ctr))
    return fn


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def construct(piece, custom_types, resource_module, module_name, attr):
    attr_res_name = attr.resource_name or attr.name
    dir_res_name = camel_to_snake(attr_res_name) + '_d'
    construct_module_dir(custom_types, resource_module, type_module_name=module_name, target_res_name=dir_res_name)

    command_res_t = resource_type_producer(htypes.impl.object_command_impl)
    command_def = command_res_t.definition_t(
        function=attr_res_name,
        params=attr.param_list,
        dir=dir_res_name,
        )
    command_res_name = f'{attr_res_name}.command'
    resource_module.set_definition(command_res_name, command_res_t, command_def)

    # Called for every command, but results with single resource.
    object_commands_d_res_name = construct_object_commands_dir(resource_module)

    association_res_t = resource_type_producer(htypes.lcs.lcs_set_association)
    association_def = association_res_t.definition_t(
        dir=(object_commands_d_res_name,),
        value=command_res_name,
        )
    resource_module.add_association_def(association_res_t, association_def)
