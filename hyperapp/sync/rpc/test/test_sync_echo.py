import queue
import logging
from contextlib import contextmanager
from pathlib import Path

import pytest

from hyperapp.common.htypes import HException
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
        'rpc.servant_path',
        'sync.rpc.rpc_call',
        'sync.rpc.rpc_endpoint',
        'sync.subprocess',
        ]


class Servant:

    def __init__(self, echo_servant_queue, peer_registry, servant_path_from_data):
        self._echo_servant_queue = echo_servant_queue
        self._peer_registry = peer_registry
        self._servant_path_from_data = servant_path_from_data

    def run(self, request, echo_peer_ref, echo_servant_path_refs):
        echo_peer = self._peer_registry.invite(echo_peer_ref)
        echo_servant_path = self._servant_path_from_data(echo_servant_path_refs)
        self._echo_servant_queue.put((echo_peer, echo_servant_path))


@pytest.fixture
def echo_set_up(services, htypes):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    servant_name = 'run_test'
    servant_path = services.servant_path().registry_name(servant_name).get_attr('run')

    rpc_endpoint = services.rpc_endpoint()
    services.endpoint_registry.register(master_identity, rpc_endpoint)

    echo_servant_queue = queue.Queue()
    servant = Servant(echo_servant_queue, services.peer_registry, services.servant_path_from_data)
    rpc_endpoint.register_servant(servant_name, servant)

    rpc_call_factory = services.rpc_call

    master_service_bundle = services.ref_collector([master_peer_ref, *servant_path.as_data]).bundle
    master_service_bundle_cdr = packet_coders.encode('cdr', master_service_bundle)

    master_peer_ref_cdr_list = [packet_coders.encode('cdr', master_peer_ref)]

    @contextmanager
    def make_rpc_call(method_name):
        subprocess = services.subprocess(
            'subprocess',
            additional_module_dirs=[Path(__file__).parent],
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
            echo_peer, echo_servant_path = echo_servant_queue.get(timeout=20)
            log.info("Got echo servant: %s %s.", echo_peer, echo_servant_path)
            rpc_call = rpc_call_factory(rpc_endpoint, echo_peer, echo_servant_path.get_attr(method_name), master_identity)
            yield rpc_call
        log.info("Subprocess is finished.")

    return make_rpc_call


def test_successful_call(echo_set_up):
    with echo_set_up('echo') as rpc_call:
        result = rpc_call('Hello')
        log.info("Got echo result: %s", result)
        assert result == 'Hello to you too'


def test_unexpected_error(htypes, echo_set_up):
    with echo_set_up('raise_unexpected_error') as rpc_call:
        with pytest.raises(HException) as excinfo:
            result = rpc_call()
        log.info("Got exception: %s", excinfo)
        assert str(excinfo.value) == "internal_error(message='Some unexpected error')"


def test_test_error(htypes, echo_set_up):
    with echo_set_up('raise_test_error') as rpc_call:
        with pytest.raises(HException) as excinfo:
            result = rpc_call()
        log.info("Got exception: %s", excinfo)
        assert str(excinfo.value) == "test_error(message='Some error')"
