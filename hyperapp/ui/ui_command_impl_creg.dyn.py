from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def ui_command_impl_creg():
    return code_registry_ctr('ui_command_impl')
