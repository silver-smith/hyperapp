from . import htypes
from .services import (
    mark,
    )


@mark.param.ResourceModuleList
def piece():
    return htypes.resources_view.resource_module_list()


@mark.param.AssociationList
def piece():
    return htypes.resources_view.association_list()


@mark.param.ResourceModuleList.variables
def current_key():
    return 'common.mark'


@mark.param.ResourceModuleList.associations
def current_key():
    return 'common.mark'


@mark.param.ResourceModuleVarList
def piece():
    return htypes.resources_view.resource_module_var_list(
        module_name='common.mark',
        )


@mark.param.ResourceModuleAssociationList
def piece():
    return htypes.resources_view.resource_module_association_list(
        module_name='common.dyn_code_registry',  # Has associations.
        )
