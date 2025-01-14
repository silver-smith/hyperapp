from .services import (
    code_registry_ctr,
    )


def route_registry(config):
    return code_registry_ctr('route_registry', config)
