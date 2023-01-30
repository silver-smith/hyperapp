from . import htypes
from .services import (
    local_types,
    mark,
    resource_module_factory,
    resource_registry_factory,
    )


@mark.param.construct
def piece():
    return None


@mark.param.construct
def custom_types():
    return local_types


@mark.param.construct
def resource_module():
    registry = resource_registry_factory()
    module = resource_module_factory(registry, 'object_command_ctr_fixtures')
    module['sample_module'] = module_res()
    return module


@mark.param.construct
def module_res():
    return htypes.python_module.python_module(
        module_name='sample_module',
        source='',
        file_path='/sample_module.dyn.py',
        import_list=(),
        )


@mark.param.construct
def attr():
    return htypes.inspect.fn_attr(
        name='sample_attr',
        module=None,
        resource_name=None,
        constructors=(),
        param_list=('sample_param',),
        )
