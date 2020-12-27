import pytest

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import cdr_coders  # self-registering


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'error',
        'hyper_ref',
        'resource',
        'module',
        'packet',
        'rsa_identity',
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.visitor',
        'common.ref_collector',
        'common.remoting.identity',
        'common.remoting.rsa_identity',
        'server.work_dir',
        'server.subprocess',
        ]


def test_send_subprocess_parcel(services):
    rsa_identity_module = services.name2module['common.remoting.rsa_identity']
    my_identity = rsa_identity_module.RsaIdentity.generate(fast=True)
    my_peer_ref = services.ref_registry.distil(my_identity.peer.piece)
    ref_collector = services.ref_collector_factory()
    my_peer_bundle = ref_collector.make_bundle([my_peer_ref])
    my_peer_bundle_cdr = packet_coders.encode('cdr', my_peer_bundle)

    subprocess = services.subprocess(
        'test_subprocess',
        type_module_list=[
            'error',
            'hyper_ref',
            'resource',
            'module',
            'packet',
            'rsa_identity',
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            'common.unbundler',
            'common.remoting.identity',
            'common.remoting.rsa_identity',
            'sync.transport.transport',
            'sync.transport.test.send_subprocess_parcel',
            ],
        config = {
            'sync.transport.test.send_subprocess_parcel': {'master_peer_bundle_cdr': my_peer_bundle_cdr},
            },
        master_peer_ref_list=[my_peer_ref],
        )
    with subprocess:
        pass
