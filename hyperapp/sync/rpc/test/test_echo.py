import logging

import pytest

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'rsa_identity',
        'rpc',
        'test_rpc',
        'echo',
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.visitor',
        'common.ref_collector',
        'common.unbundler',
        'common.remoting.identity',
        'common.remoting.rsa_identity',
        'server.work_dir',
        'server.async_stop',
        'sync.transport.transport',
        'sync.transport.endpoint',
        'server.subprocess_connection',
        'server.subprocess',
        ]


def test_echo(services, htypes):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    test_echo_iface_ref = services.types.reverse_resolve(htypes.test_rpc.test_echo_iface)
    master_service = htypes.rpc.endpoint(
        peer_ref=master_peer_ref,
        iface_ref=test_echo_iface_ref,
        object_id='run_test',
        )
    master_service_ref = services.mosaic.put(master_service)

    ref_collector = services.ref_collector_factory()
    master_service_bundle = ref_collector.make_bundle([master_service_ref])
    master_service_bundle_cdr = packet_coders.encode('cdr', master_service_bundle)

    master_peer_ref_cdr_list = [packet_coders.encode('cdr', master_peer_ref)]

    subprocess = services.subprocess(
        'subprocess',
        type_module_list=[
            'rsa_identity',
            'rpc',
            'test_rpc',
            'echo',
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            'common.unbundler',
            'common.remoting.identity',
            'common.remoting.rsa_identity',
            'server.async_stop',
            'sync.transport.transport',
            'server.subprocess_connection',
            'server.subprocess_child',
            'sync.rpc.rpc_proxy',
            'sync.rpc.test.echo_service',
            ],
        config = {
            'sync.rpc.test.echo_service': {'master_service_bundle_cdr': master_service_bundle_cdr},
            'server.subprocess_child': {'master_peer_ref_cdr_list': master_peer_ref_cdr_list},
            },
        )
    with pytest.raises(NotImplementedError) as excinfo:
        with subprocess:
            pass
        log.info("Subprocess is finished.")
    assert str(excinfo.value) == 'todo'
