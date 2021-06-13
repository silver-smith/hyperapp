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
        'sync.rpc.rpc_proxy',
        'sync.rpc.rpc_endpoint',
        'sync.subprocess',
        ]


class Servant:

    def __init__(self, echo_response_queue, mosaic, rpc_proxy, rpc_endpoint):
        self._echo_response_queue = echo_response_queue
        self._mosaic = mosaic
        self._rpc_proxy = rpc_proxy
        self._rpc_endpoint = rpc_endpoint

    def run(self, request, echo_service_ref):
        echo_service = self._mosaic.resolve_ref(echo_service_ref).value
        echo = self._rpc_proxy(request.receiver_identity, self._rpc_endpoint, echo_service)
        response = echo.echo('Hello')
        self._echo_response_queue.put(response)


def test_sync_echo(services, htypes):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    object_id = 'run_test'
    test_echo_iface_ref = services.types.reverse_resolve(htypes.test_rpc.test_echo_iface)
    master_service = htypes.rpc.endpoint(
        peer_ref=master_peer_ref,
        iface_ref=test_echo_iface_ref,
        object_id=object_id,
        )
    master_service_ref = services.mosaic.put(master_service)

    rpc_endpoint = services.rpc_endpoint()
    services.endpoint_registry.register(master_identity, rpc_endpoint)

    echo_response_queue = queue.Queue()
    servant = Servant(echo_response_queue, services.mosaic, services.rpc_proxy, rpc_endpoint)
    rpc_endpoint.register_servant(object_id, servant)

    master_service_bundle = services.ref_collector([master_service_ref]).bundle
    master_service_bundle_cdr = packet_coders.encode('cdr', master_service_bundle)

    master_peer_ref_cdr_list = [packet_coders.encode('cdr', master_peer_ref)]

    subprocess = services.subprocess(
        'subprocess',
        additional_code_module_dirs=[Path(__file__).parent],
        code_module_list=[
            'echo_service',
            ],
        config = {
            'echo_service': {'master_service_bundle_cdr': master_service_bundle_cdr},
            'sync.subprocess_child': {'master_peer_ref_cdr_list': master_peer_ref_cdr_list},
            },
        )
    with subprocess:
        log.info("Waiting for echo response.")
        response = echo_response_queue.get(timeout=10)
        log.info("Got echo response: %s.", response)
        assert response.response == 'Hello to you too'
    log.info("Subprocess is finished.")
