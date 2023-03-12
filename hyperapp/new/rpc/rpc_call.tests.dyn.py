from .services import (
    generate_rsa_identity,
    mark,
    mosaic,
    )
from .tested.services import rpc_call_factory


class PhonyRpcEndpoint:

    def wait_for_response(request_id, timeout_sec):
        return 'phony rpc response'


class PhonyTransport:

    def send(receiver, sender_identity, ref_list):
        pass


@mark.service
def transport():
    return PhonyTransport()


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
