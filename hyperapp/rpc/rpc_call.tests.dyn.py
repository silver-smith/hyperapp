from .services import (
    generate_rsa_identity,
    mark,
    mosaic,
    )
from .tested.code import rpc_call
from .tested.services import rpc_call_factory


class PhonyTransport:

    def send(self, receiver, sender_identity, ref_list):
        pass


@mark.service
def transport():
    return PhonyTransport()


class PhonyRpcEndpoint:

    def assign_future_to_request_id(self, request_id, future):
        future.set_result('phony rpc response')


def test_rpc_call_factory():
    sender_identity = generate_rsa_identity(fast=True)
    endpoint = PhonyRpcEndpoint()
    rpc_call = rpc_call_factory(
        rpc_endpoint=endpoint,
        receiver_peer='phony receiver peer',
        servant_ref=mosaic.put('phony servant'),
        sender_identity=sender_identity,
        )
    rpc_call(sample_param=12345)
