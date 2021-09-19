import queue
import logging
from pathlib import Path

import pytest

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return [
        'common.ref_collector',
        'transport.rsa_identity',
        'sync.transport.endpoint',
        'sync.transport.tcp',
        'rpc.servant_path',
        'sync.rpc.rpc_call',
        'sync.rpc.rpc_endpoint',
        'sync.subprocess',
        ]


class Servant:

    def __init__(self, echo_response_queue, peer_registry, servant_path_from_data, rpc_call_factory, rpc_endpoint, master_identity):
        self._echo_response_queue = echo_response_queue
        self._peer_registry = peer_registry
        self._servant_path_from_data = servant_path_from_data
        self._rpc_call_factory = rpc_call_factory
        self._rpc_endpoint = rpc_endpoint
        self._master_identity = master_identity

    def run(self, request, echo_peer_ref, echo_servant_path_refs):
        echo_peer = self._peer_registry.invite(echo_peer_ref)
        echo_servant_path = self._servant_path_from_data(echo_servant_path_refs)
        rpc_call = self._rpc_call_factory(self._rpc_endpoint, echo_peer, echo_servant_path, self._master_identity)
        result = rpc_call('Hello')
        self._echo_response_queue.put(result)


def test_async_echo(services, htypes):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    servant_name = 'run_test'
    servant_path = services.servant_path().registry_name(servant_name).get_attr('run')

    rpc_endpoint = services.rpc_endpoint()
    services.endpoint_registry.register(master_identity, rpc_endpoint)

    echo_response_queue = queue.Queue()
    servant = Servant(
        echo_response_queue, services.peer_registry, services.servant_path_from_data, services.rpc_call,
        rpc_endpoint, master_identity)
    rpc_endpoint.register_servant(servant_name, servant)

    server = services.tcp_server()
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    master_service_bundle = services.ref_collector([master_peer_ref, *servant_path.as_data]).bundle
    master_service_bundle_cdr = packet_coders.encode('cdr', master_service_bundle)

    subprocess = services.subprocess(
        'subprocess',
        additional_code_module_dirs=[Path(__file__).parent],
        code_module_list=[
            'async.event_loop',
            'async.async_main',
            'sync.transport.tcp',  # tcp_transport.route is required registered at sync route_registry.
            'async.transport.tcp',
            'echo_service',
            ],
        config = {
            'echo_service': {'master_service_bundle_cdr': master_service_bundle_cdr},
            },
        )
    with subprocess:
        log.info("Waiting for echo response.")
        result = echo_response_queue.get(timeout=20)
        log.info("Got echo result: %s.", result)
        assert result == 'Hello to you too'
    log.info("Subprocess is finished.")
