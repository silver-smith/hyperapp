from .services import (
    code_registry_ctr,
    )
from .code.mark import mark


@mark.service2
def ui_adapter_creg(config):
    return code_registry_ctr('ui_adapter_creg', config)
