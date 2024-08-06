from .services import (
    code_registry_ctr,
    )


def route_registry():
    return code_registry_ctr('sync_route')
