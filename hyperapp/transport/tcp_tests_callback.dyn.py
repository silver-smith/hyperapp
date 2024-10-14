import logging

from .code.mark import mark
from .code.system import run_system

log = logging.getLogger(__name__)


@mark.service2
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
    rpc_call = rpc_call_factory(rpc_endpoint, tcp_master_peer, my_identity, master_fn_ref)
    log.info("tcp_test_callback: Calling master:")
    rpc_call(message='hello')
    log.info("tcp_test_callback: Calling master: done")


def tcp_callback_main(system_config_piece, tcp_master_peer_piece, master_fn_ref):
    run_system(system_config_piece, 'tcp_test_callback', tcp_master_peer_piece, master_fn_ref)
