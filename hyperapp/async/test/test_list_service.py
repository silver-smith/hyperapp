import logging
import threading

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
        'rpc',
        'test_list_service',
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
        'transport.tcp',
        'sync.work_dir',
        'sync.async_stop',
        'sync.transport.route_table',
        'sync.transport.transport',
        'sync.transport.endpoint',
        'sync.subprocess_connection',
        'sync.subprocess',
        'sync.transport.tcp',
        'sync.rpc.rpc_proxy',
        'sync.rpc.rpc_endpoint',
        ]


class Servant:

    def __init__(self, row_t, servent_called_event):
        self._row_t = row_t
        self._servent_called_event = servent_called_event

    def get(self, request):
        self._servent_called_event.set()
        return [
            self._row_t(1, ['first row', 'first value']),
            self._row_t(2, ['second row', 'second value']),
            self._row_t(3, ['third row', 'third value']),
            ]


def test_async_echo(services, htypes):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    list_service = htypes.test_list_service.test_list_service
    iface_ref = services.types.reverse_resolve(list_service.interface)
    object_id = 'test_list_service_object'
    master_service = htypes.rpc.endpoint(
        peer_ref=master_peer_ref,
        iface_ref=iface_ref,
        object_id=object_id,
        )
    master_service_ref = services.mosaic.put(master_service)

    rpc_endpoint = services.rpc_endpoint()
    services.endpoint_registry.register(master_identity, rpc_endpoint)

    servent_called_event = threading.Event()
    servant = Servant(list_service.row_t, servent_called_event)
    rpc_endpoint.register_servant(object_id, servant)

    server = services.tcp_server()
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    master_service_bundle = services.ref_collector([master_service_ref]).bundle
    master_service_bundle_cdr = packet_coders.encode('cdr', master_service_bundle)

    subprocess = services.subprocess(
        'subprocess',
        type_module_list=[
            'rsa_identity',
            'transport',
            'tcp_transport',
            'rpc',
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            'common.unbundler',
            'transport.identity',
            'transport.rsa_identity',
            'transport.route_table',
            'transport.tcp',
            'sync.async_stop',
            'sync.transport.route_table',
            'sync.transport.transport',
            'sync.transport.tcp',  # Provide tcp route for sync route table
            'sync.transport.endpoint',
            'sync.subprocess_connection',
            'sync.subprocess_child',
            'async.event_loop',
            'async.async_main',
            'async.ui.commander',
            'async.ui.module',
            'async.async_web',
            'async.async_registry',
            'async.code_registry',
            'async.transport.route_table',
            'async.transport.transport',
            'async.transport.endpoint',
            'async.transport.tcp',
            'async.rpc.rpc_proxy',
            'async.rpc.rpc_endpoint',
            'async.test.list_service_client',
            ],
        config = {
            'async.test.list_service_client': {'master_service_bundle_cdr': master_service_bundle_cdr},
            },
        )
    with subprocess:
        log.info("Waiting for 'get' request.")
        succeeded = servent_called_event.wait(timeout=10)
        log.info("Waiting for 'get' request: done: %s", succeeded)
        assert succeeded
