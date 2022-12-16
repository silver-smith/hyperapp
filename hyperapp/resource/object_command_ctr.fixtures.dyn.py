from . import htypes
from .services import (
    local_types,
    resource_module_factory,
    )
from .code.resource_registry import ResourceRegistry
from .code.marker import param


def _dummy_fn():
    pass


param.object_command.fn = _dummy_fn

param.camel_to_snake.name = ''

param.construct.piece = None
param.construct.custom_types = local_types


@param.construct
def resource_module():
    return resource_module_factory(
        resource_registry=ResourceRegistry(),
        name='sample_resource_module',
        path='/non-existend-dir/sample_module.resources.yaml',
        load_from_file=False,
        )


param.construct.module_name = 'object_command_ctr_fixtures'
param.construct.attr = htypes.inspect.fn_attr(
    name='sample_fn',
    module=None,
    resource_name=None,
    constructors=[],
    param_list=[],
    )
