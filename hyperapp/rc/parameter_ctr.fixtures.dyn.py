from . import htypes
from .services import (
    mark,
    resource_module_factory,
    resource_registry_factory,
    )


@mark.param.construct
def piece():
    return htypes.rc_constructors.parameter(
        path=('some_function', 'param'),
        )


@mark.param.construct
def custom_types():
    return None


@mark.param.construct
def name_to_res():
    registry = resource_registry_factory()
    module = resource_module_factory(registry, 'sample_resource_module')
    module['sample_module'] = module_res()
    return module


@mark.param.construct
def module_res():
    return htypes.builtin.python_module(
        module_name='sample_module',
        source='',
        file_path='/sample_module.dyn.py',
        import_list=(),
        )


@mark.param.construct
def attr():
    return htypes.inspect.attr(
        name='sample_attr',
        module=None,
        constructors=(),
        )
