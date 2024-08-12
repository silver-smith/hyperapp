import logging
from functools import partial

from .services import (
    mosaic,
    stop_signal,
    )
from .code.subprocess_transport import SubprocessRoute
from .code.reconstructors import register_reconstructors

log = logging.getLogger(__name__)


def _stop():
    stop_signal.set()


def rpc_server_main(
        bundler, peer_registry, route_table, generate_rsa_identity, endpoint_registry, rpc_endpoint, rpc_call_factory, subprocess_transport,
        connection, received_refs, name, master_peer_piece, master_servant_ref, subprocess_id):
    my_name = f"Subprocess rpc server {name}"
    log.info("%s: Init", my_name)

    register_reconstructors()

    master_peer = peer_registry.animate(master_peer_piece)
    master_peer_ref = mosaic.put(master_peer_piece)
    route = SubprocessRoute(bundler, 'master', received_refs, connection)
    route_table.add_route(master_peer_ref, route)

    my_identity = generate_rsa_identity(fast=True)
    my_peer_ref = mosaic.put(my_identity.peer.piece)

    endpoint_registry.register(my_identity, rpc_endpoint)

    subprocess_transport.add_server_connection('master', connection, received_refs, on_eof=_stop, on_reset=_stop)

    rpc_call = rpc_call_factory(master_peer, my_identity, master_servant_ref, timeout_sec=None)

    log.info("%s: Calling callback %s", my_name, rpc_call)
    rpc_call(subprocess_name=name, subprocess_id=subprocess_id, subprocess_peer=my_identity.peer.piece)

    log.info("%s: Started", my_name)
    stop_signal.wait()
    log.info("%s: Stopping", my_name)
