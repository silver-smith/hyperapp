import logging
from collections import defaultdict

from .services import (
    web,
    )

log = logging.getLogger(__name__)


class RouteTable:

    def __init__(self, service_name, config, route_creg):
        self._service_name = service_name
        self._config = config
        self._route_creg = route_creg
        self._peer2route_list = defaultdict(list)

    def add_route(self, peer, route):
        self._peer2route_list[peer.piece].append(route)
        if route.piece is None:
            return  # Local route.
        self._config[peer.piece] = route.piece

    def peer_route_list(self, peer):
        route_list = self._peer2route_list.get(peer.piece)
        if route_list:
            return route_list
        route_piece = self._config[peer.piece]
        route = self._route_creg.animate(route_piece)
        return [route]


def route_table(config, route_creg):
    return RouteTable('route_table', config, route_creg)
