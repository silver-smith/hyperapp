import logging
import queue
from contextlib import contextmanager

from hyperapp.common.htypes.packet_coders import packet_coders

from .services import (
    bundler,
    generate_rsa_identity,
    endpoint_registry,
    module_dir_list,
    mosaic,
    python_object_creg,
    route_table,
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
            identity,
            process_name,
        ) as process:
        yield process


def test_tcp_call():
    master_identity = generate_rsa_identity(fast=True)
    master_peer_ref = mosaic.put(master_identity.peer.piece)

    request_queue = queue.Queue()
    endpoint_registry.register(master_identity, Endpoint(request_queue))

    server = tcp_server_factory()
    log.info("Tcp route: %r", server.route)
    route_table.add_route(master_peer_ref, server.route)

    master_peer_bundle = bundler([master_peer_ref]).bundle
    master_peer_bundle_cdr = packet_coders.encode('cdr', master_peer_bundle)

    with subprocess('test-tcp-send', master_identity) as process:
        log.info("Waiting for request.")
        request = request_queue.get(timeout=20)
        log.info("Got request: %s", request)
        assert request.receiver_identity.piece == master_identity.piece
