from .services import (
    mark,
    )
from .code.dyn_code_registry import DynCodeRegistry


@mark.service
def route_registry():
    return DynCodeRegistry('sync_route')
