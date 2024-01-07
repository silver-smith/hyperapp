from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def route_registry():
    return code_registry_ctr('sync_route')
