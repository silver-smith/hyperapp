import argparse
import logging
from pathlib import Path

from hyperapp.boot import dict_coders

from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.reconstructors import register_reconstructors

log = logging.getLogger(__name__)


DEFAULT_IDENTITY_PATH = Path.home() / '.local/share/hyperapp/server/identity.json'


def _parse_args(sys_argv):
    parser = argparse.ArgumentParser(description='Hyperapp server')
    parser.add_argument('--identity-path', type=Path, default=DEFAULT_IDENTITY_PATH, help="Path to server identity")
    return parser.parse_args(sys_argv)


@mark.service
def server_main(
        stop_signal,
        route_table,
        identity_registry,
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        file_bundle,
        tcp_server_factory,
        name_to_project,
        sys_argv,
        ):
    args = _parse_args(sys_argv)

    register_reconstructors()

    identity_bundle = file_bundle(args.identity_path)
    try:
        server_identity = identity_registry.animate(identity_bundle.load_piece())
        log.info("Server identity: loaded from: %s", identity_bundle.path)
    except FileNotFoundError:
        server_identity = generate_rsa_identity()
        identity_bundle.save_piece(server_identity.piece)
        log.info("Server identity: generated and saved to: %s", identity_bundle.path)

    server_peer_ref = mosaic.put(server_identity.peer.piece)
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
