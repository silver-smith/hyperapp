from .services import (
    code_registry_ctr,
    )
from .code.mark import mark


@mark.service2
def ui_command_impl_creg():
    return code_registry_ctr('ui_command_impl')
