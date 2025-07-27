from .services import (
    code_registry_ctr,
    )


def route_creg(config):
    return code_registry_ctr('route_creg', config)
