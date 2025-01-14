from functools import partial

from .code.route_table import RouteTable


def route_table(route_registry):
    return RouteTable('route_table', route_registry)
