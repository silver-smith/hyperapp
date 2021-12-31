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
def additional_module_dirs():
    return [Path(__file__).parent]


@pytest.fixture
def code_module_list():
    return [
        'common.ref_collector',
        'transport.rsa_identity',
        'sync.transport.route_table',
        'sync.transport.endpoint',
        'sync.transport.tcp',
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


def test_list_service(services, htypes, code):
    mosaic = services.mosaic
    endpoint_registry = services.endpoint_registry
    python_object_creg = services.python_object_creg

    master_identity = services.generate_rsa_identity(fast=True)
    master_peer_ref = mosaic.put(master_identity.peer.piece)

    int_t_ref = services.types.reverse_resolve(tInt)
    string_list_t_ref = services.types.reverse_resolve(TList(tString))

    servent_called_event = threading.Event()
    servant = Servant(htypes.test_list_service.row_t, servent_called_event)
    python_object_creg.register_actor(htypes.test_list_service.master_servant, lambda piece: servant.get)
    servant_fn_ref = mosaic.put(htypes.test_list_service.master_servant())

    list_service = htypes.service.list_service(
        peer_ref=master_peer_ref,
        servant_fn_ref=servant_fn_ref,
        dir_list=[],
        command_ref_list=[],
        key_attribute='key',
        )
    list_service_ref = mosaic.put(list_service)

    rpc_endpoint = services.rpc_endpoint_factory()
    endpoint_registry.register(master_identity, rpc_endpoint)

    server = services.tcp_server()
    log.info("Tcp route: %r", server.route)
    services.route_table.add_route(master_peer_ref, server.route)

    list_service_bundle = services.ref_collector([list_service_ref]).bundle
    list_service_bundle_cdr = packet_coders.encode('cdr', list_service_bundle)

    subprocess = services.subprocess(
        'subprocess',
        additional_module_dirs=[Path(__file__).parent],
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
