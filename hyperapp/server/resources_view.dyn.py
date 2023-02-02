from . import htypes
from .services import (
    mark,
    resource_registry,
    )


class ResourceModuleList:

    def __init__(self, piece):
        pass

    def get(self):
        item_list = []
        for module_name in resource_registry.module_list:
            module = resource_registry.get_module(module_name)
            item = htypes.resources_view.module_item(
                name=module_name,
                var_count=len(list(module)),
                association_count=len(module.associations),
                )
            item_list.append(item)
        return item_list

    def variables(self, current_key):
        return htypes.resources_view.resource_module_var_list(
            module_name=current_key,
            )

    def associations(self, current_key):
        return htypes.resources_view.resource_module_association_list(
            module_name=current_key,
            )


class AssociationList:

    def __init__(self, piece):
        pass

    def get(self):
        association_str_list = map(str, resource_registry.associations)
        return [
            htypes.resources_view.association_item(
                idx=idx,
                value=str(association),
                )
            for idx, association
            in enumerate(sorted(association_str_list))
            ]


class ResourceModuleVarList:

    def __init__(self, piece):
        self._module_name = piece.module_name

    def get(self):
        module = resource_registry.get_module(self._module_name)
        return [
            htypes.resources_view.var_item(
                name=name,
                value=str(module[name]),
                )
            for name in module
            ]


class ResourceModuleAssociationList:

    def __init__(self, piece):
        self._module_name = piece.module_name

    def get(self):
        module = resource_registry.get_module(self._module_name)
        association_str_list = map(str, module.associations)
        return [
            htypes.resources_view.association_item(
                idx=idx,
                value=str(association),
                )
            for idx, association
            in enumerate(sorted(association_str_list))
            ]


@mark.global_command
def open_resource_module_list():
    return htypes.resources_view.resource_module_list()


@mark.global_command
def open_association_list():
    return htypes.resources_view.association_list()
