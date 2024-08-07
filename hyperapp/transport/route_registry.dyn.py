from .services import (
    code_registry_ctr2,
    )


def route_registry(config):
    return code_registry_ctr2('sync_route', config)
