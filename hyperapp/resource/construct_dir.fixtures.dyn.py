from . import htypes
from .services import (
    local_types,
    mark,
    mosaic,
    resource_module_factory,
    )
from .code.resource_registry import ResourceRegistry


def _stub_resource_module():
  return resource_module_factory(
    resource_registry=ResourceRegistry(mosaic),
    name='sample_resource_module',
    )


@mark.param.construct_dir
def resource_module():
    return _stub_resource_module()


@mark.param.construct_dir
def dir_t():
    return htypes.command.object_commands_d


@mark.param.construct_dir
def target_res_name():
    return 'sample_target_resource'


@mark.param.construct_module_dir
def custom_types():
    return local_types


@mark.param.construct_module_dir
def resource_module():
    return _stub_resource_module()


@mark.param.construct_module_dir
def type_module_name():
    return 'command'


@mark.param.construct_module_dir
def target_res_name():
    return 'object_commands_d'


@mark.param.construct_object_commands_dir
def resource_module():
    return _stub_resource_module()
