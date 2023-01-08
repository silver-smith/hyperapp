from . import htypes
from .services import (
    local_types,
    mark,
    mosaic,
    resource_module_factory,
    )
from .code.resource_registry import ResourceRegistry


def _dummy_fn():
    pass


@mark.param.global_command
def fn():
    return _dummy_fn


@mark.param.camel_to_snake
def  name():
    return ''


@mark.param.construct
def piece():
    return None


@mark.param.construct
def custom_types():
    return local_types


@mark.param.construct
def resource_module():
    return resource_module_factory(
        resource_registry=ResourceRegistry(mosaic),
        name='sample_resource_module',
        )


@mark.param.construct
def module_name():
    return 'global_command_ctr_fixtures'


@mark.param.construct
def attr():
    return htypes.inspect.fn_attr(
        name='sample_fn',
        module=None,
        resource_name=None,
        constructors=[],
        param_list=[],
        )
