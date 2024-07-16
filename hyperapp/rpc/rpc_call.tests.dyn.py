from hyperapp.common.htypes import HException

from .services import (
    generate_rsa_identity,
    mark,
    mosaic,
    )
from .tested.services import rpc_call_factory


class TestException(HException):
    pass


class PhonyTransport:

    def send(self, receiver, sender_identity, ref_list):
        pass


@mark.service
def transport():
    return PhonyTransport()


class PhonyRpcEndpoint:

    def __init__(self, result=None, exception=None):
        self._result = result
        self._exception = exception

    def assign_future_to_request_id(self, request_id, future):
        if self._result is not None:
            future.set_result(self._result)
        if self._exception is not None:
            future.set_exception(self._exception)


def test_rpc_call_factory_success():
    sender_identity = generate_rsa_identity(fast=True)
    endpoint = PhonyRpcEndpoint(result="Phony rpc response")
    rpc_call = rpc_call_factory(
        rpc_endpoint=endpoint,
        receiver_peer='phony receiver peer',
        servant_ref=mosaic.put('phony servant'),
        sender_identity=sender_identity,
        )
    rpc_call(sample_param=12345)


def test_rpc_call_factory_exception():
    sender_identity = generate_rsa_identity(fast=True)
    endpoint = PhonyRpcEndpoint(exception=TestException("Phony rpc error"))
    rpc_call = rpc_call_factory(
        rpc_endpoint=endpoint,
        receiver_peer='phony receiver peer',
        servant_ref=mosaic.put('phony servant'),
        sender_identity=sender_identity,
        )
    try:
        rpc_call(sample_param=12345)
    except TestException:
        pass
    else:
        assert False, "No test exception was raised"
