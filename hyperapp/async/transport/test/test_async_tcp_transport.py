import logging
import queue

import pytest

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)

pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'rsa_identity',
        'transport',
        'tcp_transport',
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.visitor',
        'common.ref_collector',
        'common.unbundler',
        'transport.identity',
        'transport.rsa_identity',
        'transport.route_table',
        'sync.work_dir',
        'sync.async_stop',
        'sync.transport.transport',
        'sync.transport.endpoint',
        'sync.subprocess_connection',
        'sync.subprocess',
        'sync.transport.tcp',
        ]


class Endpoint:

    def __init__(self, request_queue):
        self._request_queue = request_queue

    def process(self, request):
        log.info("Test endpoint: process request %s", request)
        self._request_queue.put(request)


def test_tcp_send(services):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    request_queue = queue.Queue()
    services.endpoint_registry.register(master_identity, Endpoint(request_queue))

    server = services.tcp_server(('localhost', 0))
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    master_peer_bundle = services.ref_collector([master_peer_ref]).bundle
    master_peer_bundle_cdr = packet_coders.encode('cdr', master_peer_bundle)

    subprocess = services.subprocess(
        'subprocess',
        type_module_list=[
            'rsa_identity',
            'transport',
            'tcp_transport',
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            'common.unbundler',
            'transport.identity',
            'transport.rsa_identity',
            'transport.route_table',
            'sync.async_stop',
            'sync.transport.transport',
            'sync.subprocess_connection',
            'sync.subprocess_child',
            'sync.transport.tcp',
            # 'sync.transport.test.send',
            'async.event_loop',
            ],
        config={
            'sync.transport.test.send': {'master_peer_bundle_cdr': master_peer_bundle_cdr},
            },
        )
    with subprocess:
        log.info("Waiting for request.")
        request = request_queue.get(timeout=20)
        log.info("Got request: %s", request)
        assert request.receiver_identity.piece == master_identity.piece
