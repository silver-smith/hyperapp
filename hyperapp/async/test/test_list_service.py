import logging
import threading

import pytest

from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    list_service_t,
    )
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
        'object_type',
        'list_object_type',
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.visitor',
        'common.ref_collector',
        'common.unbundler',
        'common.list_object',
        'transport.identity',
        'transport.rsa_identity',
        'transport.route_table',
        'transport.tcp',
        'sync.work_dir',
        'sync.failure',
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
        log.info("Servant.get is called")
        self._servent_called_event.set()
        return [
            self._row_t(1, ['first row', 'first value']),
            self._row_t(2, ['second row', 'second value']),
            self._row_t(3, ['third row', 'third value']),
            ]


def test_list_service(services, htypes, code):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    int_t_ref = services.types.reverse_resolve(tInt)
    string_list_t_ref = services.types.reverse_resolve(TList(tString))
    service_ot = htypes.list_object_type.list_ot(
        command_list=[],
        key_column_id='key',
        column_list=[
            htypes.list_object_type.column('key', int_t_ref),
            htypes.list_object_type.column('value_list', string_list_t_ref),
            ],
        )
    service_ot_ref = services.mosaic.put(service_ot)
    row_t = code.list_object.list_row_t(services.mosaic, services.types, service_ot, 'test_list_service')

    object_id = 'test_list_service_object'
    list_service = list_service_t(
        type_ref=service_ot_ref,
        peer_ref=master_peer_ref,
        object_id=object_id,
        key_field='key',
        )
    list_service_ref = services.mosaic.put(list_service)

    rpc_endpoint = services.rpc_endpoint()
    services.endpoint_registry.register(master_identity, rpc_endpoint)

    servent_called_event = threading.Event()
    servant = Servant(row_t, servent_called_event)
    rpc_endpoint.register_servant(object_id, servant)

    server = services.tcp_server()
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    list_service_bundle = services.ref_collector([list_service_ref]).bundle
    list_service_bundle_cdr = packet_coders.encode('cdr', list_service_bundle)

    subprocess = services.subprocess(
        'subprocess',
        type_module_list=[
            'rsa_identity',
            'transport',
            'tcp_transport',
            'rpc',
            'object_type',
            'list_object_type',
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            'common.unbundler',
            'common.weak_key_dictionary_with_callback',
            'common.list_object',
            'transport.identity',
            'transport.rsa_identity',
            'transport.route_table',
            'transport.tcp',
            'sync.failure',
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
            'client.object_registry',
            'async.ui.object',
            'client.column',
            'client.list_object',
            'client.simple_list_object',
            'async.ui.list_service',
            'async.test.list_service_client',
            ],
        config = {
            'async.test.list_service_client': {'list_service_bundle_cdr': list_service_bundle_cdr},
            },
        )
    with subprocess:
        log.info("Waiting for 'get' request.")
        succeeded = servent_called_event.wait(timeout=10)
        log.info("Waiting for 'get' request: done: %s", succeeded)
        assert succeeded
