import logging
import threading
from pathlib import Path

import pytest

from hyperapp.common.htypes import (
    tInt,
    tString,
    TList,
    field_mt,
    record_mt,
    name_wrapped_mt,
    )
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return [
        'common.ref_collector',
        'common.item_column_list',
        'transport.rsa_identity',
        'sync.transport.route_table',
        'sync.transport.endpoint',
        'sync.transport.tcp',
        'rpc.servant_path',
        'sync.rpc.rpc_proxy',
        'sync.rpc.rpc_endpoint',
        'sync.subprocess',
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


@pytest.fixture
def row_t(services):
    int_t_ref = services.types.reverse_resolve(tInt)
    string_list_t_ref = services.types.reverse_resolve(TList(tString))
    field_list = [
        field_mt('key', int_t_ref),
        field_mt('value_list', string_list_t_ref),
        ]
    row_mt = record_mt(None, field_list)
    row_ref = services.mosaic.put(row_mt)
    named_row_ref = services.mosaic.put(name_wrapped_mt('list_service_row', row_ref))
    return services.types.resolve(named_row_ref)


def test_list_service(services, htypes, code, row_t):
    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = services.mosaic.put(master_identity.peer.piece)

    int_t_ref = services.types.reverse_resolve(tInt)
    string_list_t_ref = services.types.reverse_resolve(TList(tString))

    list_servant_name = 'test_list_service_object'
    list_servant_path = services.servant_path().registry_name(list_servant_name).get_attr('get')

    list_service = htypes.service.list_service(
        peer_ref=master_peer_ref,
        servant_path=list_servant_path.as_data(services.mosaic),
        dir_list=[],
        command_ref_list=[],
        key_column_id='key',
        column_list=code.item_column_list.item_t_to_column_list(services.types, row_t),
        )
    list_service_ref = services.mosaic.put(list_service)

    rpc_endpoint = services.rpc_endpoint()
    services.endpoint_registry.register(master_identity, rpc_endpoint)

    servent_called_event = threading.Event()
    servant = Servant(row_t, servent_called_event)
    rpc_endpoint.register_servant(list_servant_name, servant)

    server = services.tcp_server()
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    list_service_bundle = services.ref_collector([list_service_ref]).bundle
    list_service_bundle_cdr = packet_coders.encode('cdr', list_service_bundle)

    subprocess = services.subprocess(
        'subprocess',
        additional_code_module_dirs=[Path(__file__).parent],
        code_module_list=[
            'async.event_loop',
            'async.async_main',
            'async.transport.tcp',
            'list_service_client',
            ],
        config = {
            'list_service_client': {'list_service_bundle_cdr': list_service_bundle_cdr},
            },
        )
    with subprocess:
        log.info("Waiting for 'get' request.")
        succeeded = servent_called_event.wait(timeout=10)
        log.info("Waiting for 'get' request: done: %s", succeeded)
        assert succeeded
