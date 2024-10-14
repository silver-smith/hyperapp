from .code.mark import mark
from .tested.code import tcp_tests_callback


@mark.fixture
def rpc_call_factory(rpc_endpoint, tcp_master_peer, my_identity, master_fn_ref):
    def rpc_call(*args, **kw):
        pass
    return rpc_call


def test_callback_service(generate_rsa_identity, tcp_test_callback):
    tcp_master_identity = generate_rsa_identity(fast=True)
    tcp_test_callback(
        tcp_master_peer_piece=tcp_master_identity.peer.piece,
        master_fn_ref=None,
        )
