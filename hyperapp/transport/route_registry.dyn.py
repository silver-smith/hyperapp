from .services import (
    code_registry_ctr2,
    )


def route_registry(config):
    return code_registry_ctr2('route_registry', config)
