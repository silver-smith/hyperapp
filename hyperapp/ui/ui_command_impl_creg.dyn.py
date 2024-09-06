from .services import code_registry_ctr2
from .code.mark import mark


@mark.service2
def ui_command_impl_creg(config):
    return code_registry_ctr2('ui_command_impl', config)
