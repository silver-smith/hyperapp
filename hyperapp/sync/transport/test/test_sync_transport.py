import pytest

from hyperapp.common.htypes.packet_coders import packet_coders
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
        'server.work_dir',
        'server.subprocess',
        ]


def test_send_subprocess_parcel(services):
    rsa_identity_module = services.name2module['common.remoting.rsa_identity']
    my_identity = rsa_identity_module.RsaIdentity.generate(fast=True)
    my_peer_ref = services.ref_registry.distil(my_identity.peer.piece)
    my_peer_ref_cdr = packet_coders.encode('cdr', my_peer_ref)

    subprocess = services.subprocess(
        'test_subprocess',
        type_module_list=[
            'rsa_identity',
            ],
        code_module_list=[
            'common.remoting.identity',
            'common.remoting.rsa_identity',
            'sync.transport.transport',
            'sync.transport.test.send_subprocess_parcel',
            ],
        config = {
            'sync.transport.test.send_subprocess_parcel': {'master_peer_ref_cdr': my_peer_ref_cdr},
            },
        master_peer_ref_list=[my_peer_ref],
        )
    with pytest.raises(AssertionError) as excinfo:
        with subprocess:
            pass
    assert str(excinfo.value) == 'todo'
