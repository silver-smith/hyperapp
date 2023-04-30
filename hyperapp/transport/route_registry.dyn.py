from .services import (
    mark,
    types,
    web,
    )
from .code.dyn_code_registry import DynCodeRegistry


@mark.service
def route_registry():
    return DynCodeRegistry('sync_route', services.web, services.types)
