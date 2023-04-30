from functools import partial

from .services import (
    aux_bundler_hooks,
    aux_unbundler_hooks,
    mark,
    mosaic,
    peer_registry,
    route_registry,
    )
from .code.route_table import RouteTable


@mark.service
def route_table():
    table = RouteTable()
    aux_bundler_hooks.append(partial(
        table.aux_bundler_hook, mosaic, peer_registry))
    aux_unbundler_hooks.append(partial(
        table.aux_ref_unbundler_hook, route_registry))
    return table
