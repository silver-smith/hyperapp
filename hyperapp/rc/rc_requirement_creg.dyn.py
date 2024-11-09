from .services import (
    code_registry_ctr,
    )


def rc_requirement_creg(config):
    return code_registry_ctr('rc_requirement_creg', config)
