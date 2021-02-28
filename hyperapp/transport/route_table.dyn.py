import logging
from collections import defaultdict

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class RouteTable:

    def __init__(self):
        self._peer2route = defaultdict(list)  # ref -> route list

    def add_route(self, peer_ref, route):
        self._peer2route[peer_ref].append(route)

    def peer_route_list(self, peer_ref):
        return self._peer2route[peer_ref]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._mosaic = services.mosaic
        self._peer_registry = services.peer_registry
        self._route_registry = CodeRegistry('route', services.web, services.types)
        self._route_table = RouteTable()
        services.route_registry = self._route_registry
        services.route_table = self._route_table
        services.aux_ref_collector_hooks.append(self.route_collector_hook)
        services.aux_ref_unbundler_hooks.append(self.route_unbundler_hook)

    def route_collector_hook(self, ref, t, value):
        if not self._peer_registry.type_registered(t):
            return
        for route in self._route_table.peer_route_list(ref):
            piece = route.piece
            if piece is not None:
                route_ref = self._mosaic.put(piece)
                route_association = htypes.transport.route_association(ref, route_ref)
                yield self._mosaic.put(route_association)

    def route_unbundler_hook(self, ref, t, value):
        if t != htypes.transport.route_association:
            return
        route = self._route_registry.invite(value.route_ref)
        self._route_table.add_route(value.peer_ref, route)
