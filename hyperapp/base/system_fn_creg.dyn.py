from .services import code_registry_ctr


def system_fn_creg(config):
    return code_registry_ctr('system_fn_creg', config)
