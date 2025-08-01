import logging

from hyperapp.boot.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import tcp_transport

log = logging.getLogger(__name__)


def test_route_from_piece(tcp_connection_factory):
    piece = htypes.tcp_transport.route(host='', port=0)
    route = tcp_transport.Route.from_piece(piece, tcp_connection_factory)
    assert isinstance(route, tcp_transport.Route)


_callback_message = []


def my_callback(message):
    log.info("Callback with: %r", message)
    _callback_message.append(message)


@mark.fixture
def tcp_test_callback(
        peer_creg,
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        rpc_call_factory,
        tcp_master_peer_piece,
        master_fn_ref,
        message,
        ):
    log.info("tcp_test_callback: entered")
    tcp_master_peer = peer_creg.animate(tcp_master_peer_piece)
    my_identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(my_identity, rpc_endpoint)
    rpc_call = rpc_call_factory(tcp_master_peer, my_identity, master_fn_ref)
    log.info("tcp_test_callback: Calling master:")
    rpc_call(message=message)
    log.info("tcp_test_callback: Calling master: done")


def test_tcp_call(
        route_table,
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        subprocess_rpc_server_running,
        tcp_server_factory,
        ):
    log.info("Test TCP call")

    master_identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(master_identity, rpc_endpoint)

    tcp_master_identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(tcp_master_identity, rpc_endpoint)

    server = tcp_server_factory(bind_address=None)

    with subprocess_rpc_server_running('test-tcp-send', master_identity) as process:
        log.info("Started: %r", process)

        # Should add route after rpc server is started.
        # Otherwise, route will be transferred with full config passed to server on start.
        # And test will work even if route association is not bundled with request.
        log.info("Tcp route: %r", server.route)
        route_table.add_route(tcp_master_identity.peer, server.route)

        process.service_call('tcp_test_callback')(
            tcp_master_peer_piece=tcp_master_identity.peer.piece,
            master_fn_ref=pyobj_creg.actor_to_ref(my_callback),
            message='hello',
        )
        assert _callback_message == ['hello']
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)
