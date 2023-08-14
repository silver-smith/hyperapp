from functools import partial

from .services import (
    mark,
    route_registry,
    )
from .code.route_table import RouteTable


@mark.service
def route_table():
    return RouteTable(route_registry)
