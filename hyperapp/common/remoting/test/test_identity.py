import pytest

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

def test_rsa_identity(services):
    rsa_identity_module = services.name2module['common.remoting.rsa_identity']
    identity_1 = rsa_identity_module.RsaIdentity.generate(fast=True)
    identity_2 = services.identity_registry.animate(identity_1.piece)
    assert identity_1.piece == identity_2.piece
