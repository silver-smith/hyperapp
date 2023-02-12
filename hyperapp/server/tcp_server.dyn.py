import logging

from .services import (
    mosaic,
    route_table,
    server_identity,
    tcp_server_factory,
    )

log = logging.getLogger(__name__)


def tcp_server(bind_address):
    server_peer_ref = mosaic.put(server_identity.peer.piece)
    server = tcp_server_factory(bind_address)
    route_table.add_route(server_peer_ref, server.route)
    log.info("Server tcp route: %r", server.route)
    return server
