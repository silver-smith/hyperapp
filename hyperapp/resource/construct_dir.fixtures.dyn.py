from .services import (
    resource_module_factory,
    )
from .marker import param


def _stub_resource_module():
  return resource_module_factory(
    resource_module_registry={},
    name='sample_resource_module',
    path='/non-existend-dir/sample_module.resources.yaml',
    load_from_file=False,
    )


param.construct_dir.resource_module = _stub_resource_module()
param.construct_dir.target_res_name = 'sample_target_resource'
param.construct_dir.dir_t_res_name = 'sample_target_dir'

param.construct_module_dir.resource_module = _stub_resource_module()
param.construct_module_dir.type_module_name = 'sample_type_module_name'
param.construct_module_dir.target_res_name = 'sample_target_resource'

param.construct_object_commands_dir.resource_module = _stub_resource_module()
