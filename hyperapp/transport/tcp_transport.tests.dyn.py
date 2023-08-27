import logging

from hyperapp.common.htypes.packet_coders import packet_coders

from .services import (
    bundler,
    fn_to_ref,
    generate_rsa_identity,
    endpoint_registry,
    module_dir_list,
    mosaic,
    route_table,
    rpc_endpoint_factory,
    subprocess_rpc_server_running,
    )
from .code.tcp_tests_callback import tcp_callback
from .tested.services import tcp_server_factory

log = logging.getLogger(__name__)


_callback_message = []


def my_callback(message):
    log.info("Callback with: %r", message)
    _callback_message.append(message)


def test_tcp_call():
    log.info("Test TCP call")
    rpc_endpoint = rpc_endpoint_factory()

    master_identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(master_identity, rpc_endpoint)

    tcp_master_identity = generate_rsa_identity(fast=True)
    tcp_master_peer_ref = mosaic.put(tcp_master_identity.peer.piece)
    endpoint_registry.register(tcp_master_identity, rpc_endpoint)

    server = tcp_server_factory()
    log.info("Tcp route: %r", server.route)
    route_table.add_route(tcp_master_peer_ref, server.route)

    with subprocess_rpc_server_running('test-tcp-send', rpc_endpoint, master_identity) as process:
        process.rpc_call(tcp_callback)(
            tcp_master_peer_piece=tcp_master_identity.peer.piece,
            master_fn_ref=fn_to_ref(my_callback),
        )
        assert _callback_message == ['hello']
