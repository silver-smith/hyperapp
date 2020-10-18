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
        'common.remoting.identity',
        'common.remoting.rsa_identity',
        ]


@pytest.fixture
def rsa_identity(services):
    rsa_identity_module = services.name2module['common.remoting.rsa_identity']
    return rsa_identity_module.RsaIdentity.generate(fast=True)


def test_rsa_identity(services, rsa_identity):
    identity_2 = services.identity_registry.animate(rsa_identity.piece)
    assert rsa_identity.piece == identity_2.piece


def test_rsa_peer(services, rsa_identity):
    peer_1 = rsa_identity.peer
    peer_2 = services.peer_registry.animate(peer_1.piece)
    assert peer_1.piece == peer_2.piece


def test_rsa_parcel(services):
    rsa_identity_module = services.name2module['common.remoting.rsa_identity']
    my_identity = rsa_identity_module.RsaIdentity.generate(fast=True)
    peer_identity = rsa_identity_module.RsaIdentity.generate(fast=True)
    bundle = bundle_t(roots=[], capsule_list=[], route_list=[])
    peer_identity.peer.make_parcel(bundle, my_identity, services.ref_registry)
