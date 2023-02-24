from .services import (
    generate_rsa_identity,
    peer_registry,
    transport,
    )


def send_empty_parcel(master_peer_ref):
    master_peer = peer_registry.invite(master_peer_ref)
    my_identity = generate_rsa_identity(fast=True)

    transport.send(master_peer, my_identity, [])
