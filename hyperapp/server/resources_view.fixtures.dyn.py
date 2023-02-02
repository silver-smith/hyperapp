from . import htypes
from .services import (
    mark,
    )


@mark.param.ResourceModuleList
def piece():
    return htypes.resources_view.resource_module_list()


@mark.param.ResourceModuleList.open
def current_key():
    return 'common.mark'


@mark.param.ResourceModuleVarList
def piece():
    return htypes.resources_view.resource_module_var_list(
        module_name='common.mark',
        )
