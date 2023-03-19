from .services import (
    generate_rsa_identity,
    mosaic,
    )
from .tested.services import rpc_call_factory


class PhonyRpcEndpoint:

    def wait_for_response(self, request_id, timeout_sec):
        return 'phony rpc response'


def test_rpc_call_factory():
    sender_identity = generate_rsa_identity(fast=True)
    endpoint = PhonyRpcEndpoint()
    rpc_call = rpc_call_factory(
        rpc_endpoint=endpoint,
        receiver_peer='phony receiver peer',
        servant_ref=mosaic.put('phony servant'),
        sender_identity=sender_identity,
        )
    rpc_call()
