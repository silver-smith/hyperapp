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
def additional_module_dirs():
    return [Path(__file__).parent]


@pytest.fixture
def code_module_list():
    return [
        'common.ref_collector',
        'transport.rsa_identity',
        'sync.transport.endpoint',
        'sync.transport.tcp',
        'resource.registry',
        'resource.resource_module',
        'resource.legacy_module',
        'resource.attribute',
        'resource.call',
        'sync.rpc.rpc_call',
        'sync.rpc.rpc_endpoint',
        'sync.subprocess',
        ]


class Servant:

    def __init__(self, echo_servant_queue):
        self._echo_servant_queue = echo_servant_queue

    def run(self, request, echo_peer_ref):
        self._echo_servant_queue.put(echo_peer_ref)


@pytest.fixture
def echo_set_up(services, htypes):
    mosaic = services.mosaic
    peer_registry = services.peer_registry
    rpc_call_factory = services.rpc_call_factory

    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = mosaic.put(master_identity.peer.piece)

    rpc_endpoint = services.rpc_endpoint_factory()
    services.endpoint_registry.register(master_identity, rpc_endpoint)

    echo_servant_queue = queue.Queue()
    servant = Servant(echo_servant_queue)
    services.python_object_creg.register_actor(htypes.echo_service.master_servant, lambda piece: servant.run)
    master_servant_ref = mosaic.put(htypes.echo_service.master_servant())

    echo_servant = services.resource_module_registry['echo_service']['echo_servant']
    echo_servant_ref = mosaic.put(echo_servant)

    server = services.tcp_server()
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    master_service_bundle = services.ref_collector([master_peer_ref, master_servant_ref]).bundle
    master_service_bundle_cdr = packet_coders.encode('cdr', master_service_bundle)

    subprocess = services.subprocess(
        'subprocess',
        additional_module_dirs=[Path(__file__).parent],
        code_module_list=[
            'async.event_loop',
            'async.async_main',
            'sync.transport.tcp',  # tcp_transport.route is required registered at sync route_registry.
            'async.transport.tcp',
            'resource.async.registry',
            'resource.async.legacy_module',
            'resource.async.attribute',
            'resource.async.call',
            'echo_service',
            ],
        config = {
            'echo_service': {'master_service_bundle_cdr': master_service_bundle_cdr},
            },
        )

    @contextmanager
    def make_rpc_call(method_name):
        servant_fn = htypes.attribute.attribute(echo_servant_ref, method_name)
        servant_fn_ref = mosaic.put(servant_fn)

        with subprocess:
            log.info("Waiting for echo response.")
            echo_peer_ref = echo_servant_queue.get(timeout=20)
            echo_peer = peer_registry.invite(echo_peer_ref)
            log.info("Got echo peer: %s.", echo_peer)
            rpc_call = rpc_call_factory(rpc_endpoint, echo_peer, servant_fn_ref, master_identity)
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
        assert str(excinfo.value) == "server_error(message='Some unexpected error')"


def test_test_error(htypes, echo_set_up):
    with echo_set_up('raise_test_error') as rpc_call:
        with pytest.raises(HException) as excinfo:
            result = rpc_call()
        log.info("Got exception: %s", excinfo)
        assert str(excinfo.value) == "test_error(message='Some error')"
