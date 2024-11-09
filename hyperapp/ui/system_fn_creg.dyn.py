from .services import code_registry_ctr
from .code.mark import mark


@mark.service2
def system_fn_creg(config):
    return code_registry_ctr('system_fn_creg', config)
