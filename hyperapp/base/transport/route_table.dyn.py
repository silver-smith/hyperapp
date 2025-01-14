import logging
from collections import defaultdict

from hyperapp.boot.config_item_missing import ConfigItemMissingError
from hyperapp.boot.association_registry import Association

from .services import (
    association_reg,
    web,
    )

log = logging.getLogger(__name__)


class RouteTable:

    def __init__(self, service_name, route_registry):
        self._service_name = service_name
        self._route_registry = route_registry
        self._peer2route = defaultdict(set)  # ref -> route set

    def add_route(self, peer_ref, route):
        self._peer2route[peer_ref].add(route)
        if route.piece is None:
            return  # Local route.
        peer_piece = web.summon(peer_ref)
        ass = Association(
            bases=[peer_piece],
            key=peer_piece,
            value=route.piece,
            )
        association_reg.register_association(ass)

    def peer_route_list(self, peer_ref):
        route_set = self._peer2route.get(peer_ref, [])
        if route_set:
            return route_set
        peer_piece = web.summon(peer_ref)
        try:
            route_piece = association_reg[peer_piece]
        except KeyError:
            raise ConfigItemMissingError(
                self._service_name, peer_piece, f"{self._service_name}: No routes to {peer_piece}")
        route = self._route_registry.animate(route_piece)
        self._peer2route[peer_ref].add(route)
        return set([route])
