import logging
import threading
from functools import partial

from .services import (
    add_subprocess_server_connection,
    endpoint_registry,
    generate_rsa_identity,
    mosaic,
    peer_registry,
    route_table,
    rpc_call_factory,
    rpc_endpoint_factory,
    stop_signal,
    )
from .code.subprocess_transport import SubprocessRoute
from .code.reconstructors import register_reconstructors

log = logging.getLogger(__name__)


def _stop(rpc_endpoint):
    rpc_endpoint.stop()
    stop_signal.set()


def rpc_server_main(connection, received_refs, name, master_peer_piece, master_servant_ref, subprocess_id):
    my_name = f"Subprocess rpc server {name}"
    log.info("%s: Init", my_name)

    register_reconstructors()

    master_peer = peer_registry.animate(master_peer_piece)
    master_peer_ref = mosaic.put(master_peer_piece)
    route = SubprocessRoute('master', received_refs, connection)
    route_table.add_route(master_peer_ref, route)

    my_identity = generate_rsa_identity(fast=True)
    my_peer_ref = mosaic.put(my_identity.peer.piece)

    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(my_identity, rpc_endpoint)

    on_close = partial(_stop, rpc_endpoint)
    add_subprocess_server_connection('master', connection, received_refs, on_eof=on_close, on_reset=on_close)

    rpc_call = rpc_call_factory(rpc_endpoint, master_peer, master_servant_ref, my_identity, timeout_sec=None)

    log.info("%s: Calling callback %s", my_name, rpc_call)
    rpc_call(subprocess_name=name, subprocess_id=subprocess_id, subprocess_peer=my_identity.peer.piece)

    log.info("%s: Started", my_name)
    stop_signal.wait()
    log.info("%s: Stopping", my_name)
