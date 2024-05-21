from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def model_command_impl_creg():
    return code_registry_ctr('model_command_impl')
