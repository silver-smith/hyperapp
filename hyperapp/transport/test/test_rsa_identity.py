import pytest

from hyperapp.common.htypes import bundle_t
from hyperapp.common import cdr_coders  # self-registering


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'rsa_identity',
        ]


@pytest.fixture
def code_module_list():
    return [
        'sync.async_stop',
        'transport.identity',
        'transport.rsa_identity',
        ]


@pytest.fixture
def rsa_identity(services):
    return services.generate_rsa_identity(fast=True)


def test_rsa_identity(services, rsa_identity):
    identity_2 = services.identity_registry.animate(rsa_identity.piece)
    assert rsa_identity.piece == identity_2.piece


def test_rsa_peer(services, rsa_identity):
    peer_1 = rsa_identity.peer
    peer_2 = services.peer_registry.animate(peer_1.piece)
    assert peer_1.piece == peer_2.piece


def test_rsa_parcel(services):
    sender_identity = services.generate_rsa_identity(fast=True)
    receiver_identity = services.generate_rsa_identity(fast=True)

    test_ref = services.mosaic.put(receiver_identity.peer.piece)

    bundle_1 = bundle_t(roots=(test_ref,), capsule_list=(), route_list=())
    parcel_1 = receiver_identity.peer.make_parcel(bundle_1, sender_identity)

    parcel_2 = services.parcel_registry.animate(parcel_1.piece)
    assert parcel_2.piece == parcel_1.piece

    assert receiver_identity.peer.piece == parcel_2.receiver.piece
    assert sender_identity.peer.piece == parcel_2.sender.piece
    
    bundle_2 = receiver_identity.decrypt_parcel(parcel_2)
    assert bundle_2 == bundle_1
