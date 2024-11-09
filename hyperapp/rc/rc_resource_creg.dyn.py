from .services import (
    code_registry_ctr,
    )


def rc_resource_creg(config):
    return code_registry_ctr('rc_resource_creg', config)
