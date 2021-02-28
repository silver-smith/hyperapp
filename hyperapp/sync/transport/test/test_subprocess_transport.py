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
        ]


class Endpoint:

    def __init__(self, request_queue):
        self._request_queue = request_queue

    def process(self, request):
        self._request_queue.put(request)


def test_send_subprocess_parcel(services):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    request_queue = queue.Queue()
    services.endpoint_registry.register(master_identity, Endpoint(request_queue))

    master_peer_bundle = services.ref_collector([master_peer_ref]).bundle
    master_peer_bundle_cdr = packet_coders.encode('cdr', master_peer_bundle)

    master_peer_ref_cdr_list = [packet_coders.encode('cdr', master_peer_ref)]

    subprocess = services.subprocess(
        'subprocess',
        type_module_list=[
            'rsa_identity',
            'transport',
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
            'sync.transport.test.send',
            ],
        config = {
            'sync.transport.test.send': {'master_peer_bundle_cdr': master_peer_bundle_cdr},
            'sync.subprocess_child': {'master_peer_ref_cdr_list': master_peer_ref_cdr_list},
            },
        )
    with subprocess:
        log.info("Waiting for request.")
        request = request_queue.get()
        log.info("Got request.")
        assert request.receiver_identity.piece == master_identity.piece
    log.info("Subprocess is finished.")


def test_subprocess_transport_echo(services):
    master_identity = services.generate_rsa_identity(fast=True)

    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    request_queue = queue.Queue()
    services.endpoint_registry.register(master_identity, Endpoint(request_queue))

    master_peer_bundle = services.ref_collector([master_peer_ref]).bundle
    master_peer_bundle_cdr = packet_coders.encode('cdr', master_peer_bundle)

    master_peer_ref_cdr_list = [packet_coders.encode('cdr', master_peer_ref)]

    subprocess = services.subprocess(
        'subprocess',
        type_module_list=[
            'rsa_identity',
            'transport',
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
            'sync.transport.endpoint',
            'sync.subprocess_connection',
            'sync.subprocess_child',
            'sync.transport.test.echo',
            ],
        config = {
            'sync.transport.test.echo': {'master_peer_bundle_cdr': master_peer_bundle_cdr},
            'sync.subprocess_child': {'master_peer_ref_cdr_list': master_peer_ref_cdr_list},
            },
        )
    with subprocess:
        log.info("Waiting for first request.")
        request_1 = request_queue.get()
        log.info("Got first request.")
        assert request_1.receiver_identity.piece == master_identity.piece

        child_peer = services.peer_registry.invite(request_1.ref_list[0])
        services.transport.send(child_peer, master_identity, [master_peer_ref])

        log.info("Waiting for second request.")
        request_2 = request_queue.get()
        log.info("Got second request.")
        assert request_2.receiver_identity.piece == master_identity.piece
        assert request_2.sender.piece == child_peer.piece

        assert request_2.ref_list[0] == master_peer_ref
        child_peer_2 = services.peer_registry.invite(request_2.ref_list[1])
        assert child_peer_2.piece == child_peer.piece

    log.info("Subprocess is finished.")
