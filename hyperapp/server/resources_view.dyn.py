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
            vars = resource_registry.module_vars(module_name)
            item = htypes.resources_view.module_item(
                name=module_name,
                var_count=len(vars),
                )
            item_list.append(item)
        return item_list

    def open(self, current_key):
        return htypes.resources_view.resource_module_var_list(
            module_name=current_key,
            )


class ResourceModuleVarList:

    def __init__(self, piece):
        self._module_name = piece.module_name

    def get(self):
        var_name_list = resource_registry.module_vars(self._module_name)
        return [
            htypes.resources_view.var_item(
                name=name,
                value=str(resource_registry[self._module_name, name]),
                )
            for name in var_name_list
            ]


@mark.global_command
def open_resource_module_list():
    return htypes.resources_view.resource_module_list()
