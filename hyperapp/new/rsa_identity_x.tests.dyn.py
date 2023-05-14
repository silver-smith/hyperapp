from hyperapp.common.htypes import bundle_t
from hyperapp.common import cdr_coders  # self-registering

from .services import (
    identity_registry_x,
    mosaic,
    parcel_registry_x,
    peer_registry_x,
    )
from .tested.services import (
    generate_rsa_identity_x,
    )


def test_rsa_identity():
    identity = generate_rsa_identity_x(fast=True)
    identity_2 = identity_registry_x.animate(identity.piece)
    assert identity.piece == identity_2.piece


def test_rsa_peer():
    identity = generate_rsa_identity_x(fast=True)
    peer_1 = identity.peer
    peer_2 = peer_registry_x.animate(peer_1.piece)
    assert peer_1.piece == peer_2.piece


def test_rsa_parcel():
    sender_identity = generate_rsa_identity_x(fast=True)
    receiver_identity = generate_rsa_identity_x(fast=True)

    test_ref = mosaic.put(receiver_identity.peer.piece)

    bundle_1 = bundle_t(roots=(test_ref,), aux_roots=(), capsule_list=())
    parcel_1 = receiver_identity.peer.make_parcel(bundle_1, sender_identity)

    parcel_2 = parcel_registry_x.animate(parcel_1.piece)
    assert parcel_2.piece == parcel_1.piece

    assert receiver_identity.peer.piece == parcel_2.receiver.piece
    assert sender_identity.peer.piece == parcel_2.sender.piece

    bundle_2 = receiver_identity.decrypt_parcel(parcel_2)
    assert bundle_2 == bundle_1
