import logging
from collections import defaultdict

from . import htypes

log = logging.getLogger(__name__)


class RouteTable:

    def __init__(self):
        self._peer2route = defaultdict(list)  # ref -> route list

    def add_route(self, peer_ref, route):
        self._peer2route[peer_ref].append(route)

    def peer_route_list(self, peer_ref):
        return self._peer2route[peer_ref]

    def aux_ref_collector_hook(self, mosaic, peer_registry, ref, t, value):
        if not peer_registry.type_registered(t):
            return
        for route in self.peer_route_list(ref):
            piece = route.piece
            if piece is not None:
                route_ref = mosaic.put(piece)
                route_association = htypes.transport.route_association(ref, route_ref)
                yield mosaic.put(route_association)

    def aux_ref_unbundler_hook(self, route_registry, ref, t, value):
        if t != htypes.transport.route_association:
            return
        route = route_registry.invite(value.route_ref)
        self.add_route(value.peer_ref, route)
