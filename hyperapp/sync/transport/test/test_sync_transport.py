import logging
import queue
import threading

import pytest

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


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


class Endpoint:

    def __init__(self, parcel_queue):
        self._parcel_queue = parcel_queue

    def process(self, parcel):
        self._parcel_queue.put(parcel)


def test_send_subprocess_parcel(services):
    master_identity = services.generate_rsa_identity(fast=True)

    master_peer_ref = services.ref_registry.distil(master_identity.peer.piece)

    parcel_queue = queue.Queue()
    services.endpoint_registry.register(master_peer_ref, Endpoint(parcel_queue))

    ref_collector = services.ref_collector_factory()
    master_peer_bundle = ref_collector.make_bundle([master_peer_ref])
    master_peer_bundle_cdr = packet_coders.encode('cdr', master_peer_bundle)

    master_peer_ref_cdr_list = [packet_coders.encode('cdr', master_peer_ref)]

    subprocess = services.subprocess(
        'subprocess',
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
            'server.async_stop',
            'sync.transport.transport',
            'server.subprocess_connection',
            'server.subprocess_child',
            'sync.transport.test.send_subprocess_parcel',
            ],
        config = {
            'sync.transport.test.send_subprocess_parcel': {'master_peer_bundle_cdr': master_peer_bundle_cdr},
            'server.subprocess_child': {'master_peer_ref_cdr_list': master_peer_ref_cdr_list},
            },
        )
    with subprocess:
        log.info("Waiting for parcel.")
        parcel = parcel_queue.get()
        log.info("Got parcel.")
        assert parcel.receiver.piece == master_identity.peer.piece
    log.info("Subprocess is finished.")


def test_subprocess_transport_echo(services):
    master_identity = services.generate_rsa_identity(fast=True)

    master_peer_ref = services.ref_registry.distil(master_identity.peer.piece)

    parcel_queue = queue.Queue()
    services.endpoint_registry.register(master_peer_ref, Endpoint(parcel_queue))

    ref_collector = services.ref_collector_factory()
    master_peer_bundle = ref_collector.make_bundle([master_peer_ref])
    master_peer_bundle_cdr = packet_coders.encode('cdr', master_peer_bundle)

    master_peer_ref_cdr_list = [packet_coders.encode('cdr', master_peer_ref)]

    subprocess = services.subprocess(
        'subprocess',
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
            'server.async_stop',
            'sync.transport.transport',
            'sync.transport.endpoint',
            'server.subprocess_connection',
            'server.subprocess_child',
            'sync.transport.test.subprocess_echo',
            ],
        config = {
            'sync.transport.test.subprocess_echo': {'master_peer_bundle_cdr': master_peer_bundle_cdr},
            'server.subprocess_child': {'master_peer_ref_cdr_list': master_peer_ref_cdr_list},
            },
        )
    with subprocess:
        log.info("Waiting for first parcel.")
        parcel_1 = parcel_queue.get()
        log.info("Got first parcel.")
        assert parcel_1.receiver.piece == master_identity.peer.piece

        bundle_1 = master_identity.decrypt_parcel(parcel_1)
        services.unbundler.register_bundle(bundle_1)
        child_peer = services.peer_registry.invite(bundle_1.roots[0])

        ref_collector = services.ref_collector_factory()
        bundle_2 = ref_collector.make_bundle([master_peer_ref])
        parcel_2 = child_peer.make_parcel(bundle_2, master_identity)
        services.transport.send(parcel_2)

        log.info("Waiting for second parcel.")
        parcel_3 = parcel_queue.get()
        log.info("Got second parcel.")
        assert parcel_3.receiver.piece == master_identity.peer.piece
        assert parcel_3.sender.piece == child_peer.piece

        bundle_3 = master_identity.decrypt_parcel(parcel_3)
        services.unbundler.register_bundle(bundle_3)
        assert bundle_3.roots[0] == master_peer_ref
        child_peer_2 = services.peer_registry.invite(bundle_3.roots[1])
        assert child_peer_2.piece == child_peer.piece

    log.info("Subprocess is finished.")
