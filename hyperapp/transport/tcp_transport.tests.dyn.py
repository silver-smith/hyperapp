import logging

from hyperapp.boot.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    module_dir_list,
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
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


def test_client_factory(tcp_client_factory):
    address = ('127.0.0.1', 8888)
    connection = tcp_client_factory(address)
    connection._socket.close()


@mark.fixture
def tcp_test_callback(
        peer_registry,
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        rpc_call_factory,
        tcp_master_peer_piece,
        master_fn_ref,
        ):
    log.info("tcp_test_callback: entered")
    tcp_master_peer = peer_registry.animate(tcp_master_peer_piece)
    my_identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(my_identity, rpc_endpoint)
    rpc_call = rpc_call_factory(tcp_master_peer, my_identity, master_fn_ref)
    log.info("tcp_test_callback: Calling master:")
    rpc_call(message='hello')
    log.info("tcp_test_callback: Calling master: done")


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
        process.service_call('tcp_test_callback')(
            tcp_master_peer_piece=tcp_master_identity.peer.piece,
            master_fn_ref=pyobj_creg.actor_to_ref(my_callback),
        )
        assert _callback_message == ['hello']
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)
