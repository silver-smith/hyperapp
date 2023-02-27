import logging
from contextlib import contextmanager

from hyperapp.common.htypes.packet_coders import packet_coders

from .services import (
    bundler,
    fn_to_ref,
    generate_rsa_identity,
    endpoint_registry,
    module_dir_list,
    mosaic,
    python_object_creg,
    route_table,
    rpc_endpoint_factory,
    subprocess_running,
    )
from .code.tcp_tests_call_back import call_back
from .tested.services import tcp_server_factory

log = logging.getLogger(__name__)


process_code_module_list = [
    'common.lcs',
    'common.lcs_service',
    'resource.legacy_type',
    'resource.legacy_module',
    'resource.legacy_service',
    'resource.python_module',
    'resource.attribute',
    'resource.call',
    'ui.impl_registry',
    'ui.global_command_list',
    ]


class Endpoint:

    def __init__(self, request_queue):
        self._request_queue = request_queue

    def process(self, request):
        log.info("Test endpoint: process request %s", request)
        self._request_queue.put(request)


@contextmanager
def subprocess(process_name, master_identity):
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(master_identity, rpc_endpoint)
    with subprocess_running(
            module_dir_list,
            process_code_module_list,
            rpc_endpoint,
            master_identity,
            process_name,
        ) as process:
        yield process


def my_callback(message):
    log.info("Callback with: %r", message)


def test_tcp_call():
    log.info("Test TCP call")
    master_identity = generate_rsa_identity(fast=True)
    master_peer_ref = mosaic.put(master_identity.peer.piece)

    tcp_master_identity = generate_rsa_identity(fast=True)
    tcp_master_peer_ref = mosaic.put(tcp_master_identity.peer.piece)

    callback_ref = fn_to_ref(call_back)
    my_callback_ref = fn_to_ref(my_callback)
    log.info("Child callback: %r, my callback: %r", callback_ref, my_callback_ref)

    server = tcp_server_factory()
    log.info("Tcp route: %r", server.route)
    route_table.add_route(tcp_master_peer_ref, server.route)

    with subprocess('test-tcp-send', master_identity) as process:
        callback_call = process.rpc_call(callback_ref)
        callback_call(tcp_master_peer_ref=tcp_master_peer_ref, master_fn_ref=my_callback_ref)
