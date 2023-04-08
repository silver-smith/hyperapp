import logging

from .services import (
    endpoint_registry,
    generate_rsa_identity,
    mosaic,
    peer_registry,
    rpc_call_factory,
    rpc_endpoint_factory,
    )

log = logging.getLogger(__name__)


def rpc_server_main(connection, name, master_peer_piece, master_servant_ref):
    my_name = f"Subprocess rpc server {name}"
    log.info("%s: Init identity", my_name)

    master_peer = peer_registry.animate(master_peer_piece)

    my_identity = generate_rsa_identity(fast=True)
    my_peer_ref = mosaic.put(my_identity.peer.piece)

    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(my_identity, rpc_endpoint)

    rpc_call = rpc_call_factory(rpc_endpoint, master_peer, master_servant_ref, my_identity, timeout_sec=20)

    log.info("%s: Calling callback %s", my_name, rpc_call)
    rpc_call()

    log.info("%s: Started", my_name)
