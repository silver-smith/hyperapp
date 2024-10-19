import logging

from hyperapp.common.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    module_dir_list,
    mosaic,
    pyobj_creg,
    )
from .code.system import run_system
from .code import tcp_tests_callback  # Just mark it as a requirement.
from .tested.code import tcp_transport

log = logging.getLogger(__name__)


def test_route_from_piece():
    piece = htypes.tcp_transport.route(host='', port=0)
    route = tcp_transport.Route.from_piece(piece)
    assert isinstance(route, tcp_transport.Route)


_callback_message = []


def my_callback(message):
    log.info("Callback with: %r", message)
    _callback_message.append(message)


def test_tcp_call(
        system_config_piece,
        route_table,
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        subprocess_rpc_server_running,
        tcp_server_factory
        ):
    log.info("Test TCP call")

    master_identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(master_identity, rpc_endpoint)

    tcp_master_identity = generate_rsa_identity(fast=True)
    tcp_master_peer_ref = mosaic.put(tcp_master_identity.peer.piece)
    endpoint_registry.register(tcp_master_identity, rpc_endpoint)

    server = tcp_server_factory(bind_address=None)
    log.info("Tcp route: %r", server.route)
    route_table.add_route(tcp_master_peer_ref, server.route)

    with subprocess_rpc_server_running('test-tcp-send', master_identity) as process:
        log.info("Started: %r", process)
        process.rpc_call(run_system)(
            config=system_config_piece,
            root_name='tcp_test_callback',
            tcp_master_peer_piece=tcp_master_identity.peer.piece,
            master_fn_ref=pyobj_creg.actor_to_ref(my_callback),
        )
        assert _callback_message == ['hello']
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)
