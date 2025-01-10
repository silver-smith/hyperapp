import logging

from hyperapp.boot.htypes import HException

from .services import (
    mosaic,
    )
from .code.mark import mark
from .tested.code import rpc_call as rpc_call_module

log = logging.getLogger(__name__)


class TestException(HException):
    pass


class PhonyTransport:

    def send(self, receiver, sender_identity, ref_list):
        log.info("Phony transport: send %s <- %s: %s", receiver, sender_identity, ref_list)


@mark.fixture
def transport():
    return PhonyTransport()


class FutureResult:

    def __init__(self):
        self._result = None
        self._exception = None

    def get_result(self):
        if self._result is not None:
            log.info("Future result: return %r", self._result)
            return self._result
        if self._exception is not None:
            log.info("Future result: raise %r", self._exception)
            raise self._exception

    def set_result(self, result):
        self._result = result

    def set_exception(self, exception):
        self._exception = exception


@mark.fixture
def future_result():
    return FutureResult()


@mark.fixture
def rpc_wait_for_future(future_result, future, timeout_sec):
    return future_result.get_result()


def test_rpc_call_factory_success(generate_rsa_identity, rpc_call_factory, future_result):
    sender_identity = generate_rsa_identity(fast=True)
    call_result = "Sample call result"
    future_result.set_result(call_result)
    rpc_call = rpc_call_factory(
        receiver_peer='phony receiver peer',
        sender_identity=sender_identity,
        servant_ref=mosaic.put('phony servant'),
        )
    result = rpc_call(sample_param=12345)
    assert result == call_result


def test_rpc_call_factory_exception(generate_rsa_identity, rpc_call_factory, future_result):
    sender_identity = generate_rsa_identity(fast=True)
    future_result.set_exception(TestException("Phony rpc error"))
    rpc_call = rpc_call_factory(
        receiver_peer='phony receiver peer',
        sender_identity=sender_identity,
        servant_ref=mosaic.put('phony servant'),
        )
    try:
        rpc_call(sample_param=12345)
    except TestException:
        pass
    else:
        assert False, "No test exception was raised"
