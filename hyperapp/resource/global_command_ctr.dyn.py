import inspect
import re

from . import htypes
from .services import (
    mosaic,
    resource_type_producer,
  )
from .constants import RESOURCE_CTR_ATTR


def global_command(fn):
    module = inspect.getmodule(fn)
    ctr_dict = module.__dict__.setdefault(RESOURCE_CTR_ATTR, {})
    ctr_list = ctr_dict.setdefault(fn.__name__, [])
    ctr = htypes.global_command_ctr.global_command_ctr()
    ctr_list.append(mosaic.put(ctr))
    return fn


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def _construct_dir(resource_module, target_res_name, dir_t_res_name):
    call_res_t = resource_type_producer(htypes.call.call)
    call_def = call_res_t.definition_t(
        function=dir_t_res_name,
        )
    resource_module.set_definition(target_res_name, call_res_t, call_def)
    resource_module.add_import(dir_t_res_name)


def _construct_module_dir(resource_module, type_module_name, target_res_name):
    dir_t_res_name = f'legacy_type.{type_module_name}:{target_res_name}'
    _construct_dir(resource_module, target_res_name, dir_t_res_name)


def construct(piece, resource_module, module_name, attr):
    attr_res_name = attr.resource_name or attr.name
    dir_res_name = camel_to_snake(attr_res_name) + '_d'
    _construct_module_dir(resource_module, type_module_name=module_name, target_res_name=dir_res_name)

    command_res_t = resource_type_producer(htypes.impl.global_command_impl)
    command_def = command_res_t.definition_t(
        function=attr_res_name,
        dir=dir_res_name,
        )
    command_res_name = f'{attr_res_name}.command'
    resource_module.set_definition(command_res_name, command_res_t, command_def)

    association_res_t = resource_type_producer(htypes.global_command.global_command_association)
    association_def = association_res_t.definition_t(
        command=command_res_name,
        )
    resource_module.add_association(association_res_t, association_def)
