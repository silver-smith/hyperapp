import argparse
import logging
from pathlib import Path

from hyperapp.boot import dict_coders

from .code.mark import mark
from .code.reconstructors import register_reconstructors

log = logging.getLogger(__name__)


DEFAULT_IDENTITY_PATH = Path.home() / '.local/share/hyperapp/server/identity.json'
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 7777


def _parse_args(sys_argv):
    parser = argparse.ArgumentParser(description='Hyperapp server')
    parser.add_argument('--identity-path', type=Path, default=DEFAULT_IDENTITY_PATH, help="Path to server identity")
    parser.add_argument('--host', default=DEFAULT_HOST, help="Bind to host")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help="Bind to port")
    return parser.parse_args(sys_argv)


@mark.service
def server_main(
        stop_signal,
        route_table,
        identity_creg,
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        file_bundle_factory,
        tcp_server_factory,
        name_to_project,
        sys_argv,
        ):
    args = _parse_args(sys_argv)

    register_reconstructors()

    identity_bundle = file_bundle_factory(args.identity_path)
    try:
        server_identity = identity_creg.animate(identity_bundle.load_piece())
        log.info("Server identity: loaded from: %s", identity_bundle.path)
    except FileNotFoundError:
        server_identity = generate_rsa_identity()
        identity_bundle.save_piece(server_identity.piece)
        log.info("Server identity: generated and saved to: %s", identity_bundle.path)

    endpoint_registry.register(server_identity, rpc_endpoint)

    bind_address = (args.host, args.port)
    server = tcp_server_factory(bind_address)
    log.info("Tcp route: %r", server.route)
    route_table.add_route(server_identity.peer, server.route)

    peer_bundle = file_bundle_factory(Path.home() / '.local/share/hyperapp/server/peer.json')
    peer_bundle.save_piece(server_identity.peer.piece)
    log.info("Server peer: saved to: %s", peer_bundle.path)

    log.info("Server: %s is listening at %s", server_identity, server.route)
    try:
        stop_signal.wait()
    except KeyboardInterrupt:
        print()  # Leave '^C' on separate line.
        log.info("Server: Stopping")
