import logging
import threading

from .services import (
    add_subprocess_server_connection,
    endpoint_registry,
    generate_rsa_identity,
    mosaic,
    peer_registry,
    route_table,
    rpc_call_factory,
    rpc_endpoint_factory,
    )
from .code.subprocess_transport import SubprocessRoute

log = logging.getLogger(__name__)

_stop_signal = threading.Event()


def _stop():
    _stop_signal.set()


def rpc_server_main(connection, name, master_peer_piece, master_servant_ref, subprocess_id):
    my_name = f"Subprocess rpc server {name}"
    log.info("%s: Init", my_name)

    add_subprocess_server_connection(name, connection, on_eof=_stop)

    master_peer = peer_registry.animate(master_peer_piece)
    master_peer_ref = mosaic.put(master_peer_piece)
    route = SubprocessRoute(name, connection)
    route_table.add_route(master_peer_ref, route)

    my_identity = generate_rsa_identity(fast=True)
    my_peer_ref = mosaic.put(my_identity.peer.piece)

    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(my_identity, rpc_endpoint)

    rpc_call = rpc_call_factory(rpc_endpoint, master_peer, master_servant_ref, my_identity, timeout_sec=20)

    log.info("%s: Calling callback %s", my_name, rpc_call)
    rpc_call(subprocess_id=subprocess_id, subprocess_peer=my_identity.peer.piece)

    log.info("%s: Started", my_name)
    _stop_signal.wait()
    log.info("%s: Stopping", my_name)
