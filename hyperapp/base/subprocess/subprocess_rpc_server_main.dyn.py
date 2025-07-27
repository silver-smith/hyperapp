import logging
from concurrent.futures import CancelledError
from functools import partial

from .code.subprocess_transport import SubprocessRoute
from .code.reconstructors import register_reconstructors

log = logging.getLogger(__name__)


def _stop(stop_signal, cancel_rpc_request_futures):
    log.info("Master connection is closed; stopping server...")
    stop_signal.set()
    cancel_rpc_request_futures()


def rpc_server_main(
        stop_signal,
        bundler,
        peer_creg,
        route_table,
        generate_rsa_identity,
        endpoint_registry,
        cancel_rpc_request_futures,
        rpc_endpoint,
        rpc_call_factory,
        subprocess_transport,
        connection,
        received_refs,
        name,
        master_peer_piece,
        master_servant_ref,
        subprocess_id,
        ):
    my_name = f"Subprocess rpc server {name}"
    log.info("%s: Init", my_name)

    register_reconstructors()

    master_peer = peer_creg.animate(master_peer_piece)
    route = SubprocessRoute(bundler, 'master', received_refs, connection)
    route_table.add_route(master_peer, route)

    my_identity = generate_rsa_identity(fast=True)

    endpoint_registry.register(my_identity, rpc_endpoint)

    on_stop = partial(_stop, stop_signal, cancel_rpc_request_futures)
    subprocess_transport.add_server_connection('master', connection, received_refs, on_eof=on_stop, on_reset=on_stop)

    rpc_call = rpc_call_factory(master_peer, my_identity, master_servant_ref, timeout_sec=None)

    log.info("%s: Calling callback %s", my_name, rpc_call)
    try:
        rpc_call(subprocess_name=name, subprocess_id=subprocess_id, subprocess_peer=my_identity.peer.piece)
    except CancelledError:
        log.info("%s: Failed to start: Master call back was cancelled", my_name)
    else:
        log.info("%s: Started", my_name)
        stop_signal.wait()
        log.info("%s: Stopping", my_name)
