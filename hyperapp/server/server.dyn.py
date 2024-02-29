import logging
from pathlib import Path

from hyperapp.common import dict_coders

from .services import (
    endpoint_registry,
    file_bundle,
    generate_rsa_identity,
    mosaic,
    identity_registry,
    peer_registry,
    route_table,
    rpc_call_factory,
    rpc_endpoint_factory,
    stop_signal,
    tcp_server_factory,
    )

log = logging.getLogger(__name__)


def _main():

    identity_bundle = file_bundle(Path.home() / '.local/share/hyperapp/server/identity.json')
    try:
        server_identity = identity_registry.animate(identity_bundle.load_piece())
        log.info("Server identity: loaded from: %s", identity_bundle.path)
    except FileNotFoundError:
        server_identity = generate_rsa_identity()
        identity_bundle.save_piece(server_identity.piece)
        log.info("Server identity: generated and saved to: %s", identity_bundle.path)

    server_peer_ref = mosaic.put(server_identity.peer.piece)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(server_identity, rpc_endpoint)

    server = tcp_server_factory()
    log.info("Tcp route: %r", server.route)
    route_table.add_route(server_peer_ref, server.route)

    peer_bundle = file_bundle(Path.home() / '.local/share/hyperapp/server/peer.json')
    peer_bundle.save_piece(server_identity.peer.piece)
    log.info("Server peer: saved to: %s", peer_bundle.path)

    log.info("Server: Started at %s", server.route)
    try:
        stop_signal.wait()
    except KeyboardInterrupt:
        print()  # Leave '^C' on separate line.
        log.info("Server: Stopping")
        return 0
