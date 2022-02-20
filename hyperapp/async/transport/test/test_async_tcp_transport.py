import logging
import queue
from pathlib import Path

import pytest

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)

pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return [
        'common.bundler',
        'transport.rsa_identity',
        'sync.transport.route_table',
        'sync.transport.endpoint',
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

    server = services.tcp_server()
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    master_peer_bundle = services.bundler([master_peer_ref]).bundle
    master_peer_bundle_cdr = packet_coders.encode('cdr', master_peer_bundle)

    subprocess = services.subprocess(
        'subprocess',
        additional_module_dirs=[Path(__file__).parent],
        code_module_list=[
            'async.event_loop',
            'async.async_main',
            'async.transport.tcp',
            'send',
            ],
        config={
            'send': {'master_peer_bundle_cdr': master_peer_bundle_cdr},
            },
        )
    with subprocess:
        log.info("Waiting for request.")
        request = request_queue.get(timeout=20)
        log.info("Got request: %s", request)
        assert request.receiver_identity.piece == master_identity.piece


def test_tcp_echo(services):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    request_queue = queue.Queue()
    services.endpoint_registry.register(master_identity, Endpoint(request_queue))

    server = services.tcp_server()
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    master_peer_bundle = services.bundler([master_peer_ref]).bundle
    master_peer_bundle_cdr = packet_coders.encode('cdr', master_peer_bundle)

    subprocess = services.subprocess(
        'subprocess',
        additional_module_dirs=[Path(__file__).parent],
        code_module_list=[
            'sync.transport.tcp',  # tcp_transport.route is required registered at sync route_registry.
            'async.event_loop',
            'async.async_main',
            'async.transport.tcp',
            'echo',
            ],
        config={
            'echo': {'master_peer_bundle_cdr': master_peer_bundle_cdr},
            },
        )
    with subprocess:
        log.info("Waiting for first request.")
        request_1 = request_queue.get(timeout=20)
        log.info("Got first request: %s", request_1)
        assert request_1.receiver_identity.piece == master_identity.piece

        child_peer = services.peer_registry.invite(request_1.ref_list[0])
        services.transport.send(child_peer, master_identity, [master_peer_ref])

        log.info("Waiting for second request.")
        request_2 = request_queue.get(timeout=20)
        log.info("Got second request: %s", request_2)
        assert request_2.receiver_identity.piece == master_identity.piece
        assert request_2.sender.piece == child_peer.piece

        assert request_2.ref_list[0] == master_peer_ref
        child_peer_2 = services.peer_registry.invite(request_2.ref_list[1])
        assert child_peer_2.piece == child_peer.piece

    log.info("Subprocess is finished.")
