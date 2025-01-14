import logging
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.endpoint import Request
from .tested.code import rpc_endpoint

log = logging.getLogger(__name__)


@mark.fixture
def transport():
    return Mock()


@mark.fixture
def _test_with(transport, rpc_endpoint, generate_rsa_identity, servant_fn):
    sender_identity = generate_rsa_identity(fast=True)
    target = htypes.rpc.function_target(
        servant_ref=pyobj_creg.actor_to_ref(servant_fn),
        params=(htypes.rpc.param('sample_param', mosaic.put("Sample param value")),),
        )
    rpc_request = htypes.rpc.request(
        request_id='Phony request id',
        target=mosaic.put(target),
        )
    request = Request(
        receiver_identity=None,
        sender=None,
        ref_list=[mosaic.put(rpc_request)],
        )
    rpc_endpoint.process(request)
    transport.send.assert_called_once()


def _return_str_list(sample_param):
    log.info("_return_str_list: %s", sample_param)
    return [
        mosaic.put("Sample result string"),
        ]


def test_str_list_response(_test_with):
    _test_with(_return_str_list)


def _raise_happ_error(sample_param):
    log.info("_raise_happ_error: %s", sample_param)
    raise htypes.rpc_endpoint_tests.sample_error("sample error message")


def test_happ_error(_test_with):
    _test_with(_raise_happ_error)


def _raise_non_happ_error(sample_param):
    log.info("_raise_non_happ_error: %s", sample_param)
    raise RuntimeError("Sample non-happ error")


def test_non_happ_error(_test_with):
    _test_with(_raise_non_happ_error)
