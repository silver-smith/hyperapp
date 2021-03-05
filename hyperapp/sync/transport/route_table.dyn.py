import logging
from functools import partial

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

from .route_table import RouteTable

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        route_registry = CodeRegistry('route', services.web, services.types)
        route_table = RouteTable()
        services.route_registry = route_registry
        services.route_table = route_table
        services.aux_ref_collector_hooks.append(partial(
            route_table.aux_ref_collector_hook, services.mosaic, services.peer_registry))
        services.aux_ref_unbundler_hooks.append(partial(
            route_table.aux_ref_unbundler_hook, route_registry))
