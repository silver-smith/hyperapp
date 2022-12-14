from . import htypes
from .services import (
    local_types,
    resource_module_factory,
    )
from .marker import param
from .resource_registry import ResourceRegistry


def _stub_resource_module():
  return resource_module_factory(
    resource_registry=ResourceRegistry(),
    name='sample_resource_module',
    path='/non-existend-dir/sample_module.resources.yaml',
    load_from_file=False,
    )


@param.construct_dir
def resource_module():
    return _stub_resource_module()


param.construct_dir.dir_t = htypes.command.object_commands_d
param.construct_dir.target_res_name = 'sample_target_resource'

param.construct_module_dir.custom_types = local_types


@param.construct_module_dir
def resource_module():
    return _stub_resource_module()


param.construct_module_dir.type_module_name = 'command'
param.construct_module_dir.target_res_name = 'object_commands_d'


@param.construct_object_commands_dir
def resource_module():
    return _stub_resource_module()
