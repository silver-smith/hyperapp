from . import htypes
from .services import (
    generate_rsa_identity,
    mark,
    mosaic,
    pyobj_creg,
    )
from .code.endpoint import Request
# from .tested.code import rpc_endpoint
from .tested.services import rpc_endpoint_factory


class PhonyTransport:

    def send(self, receiver, sender_identity, ref_list):
        pass


@mark.service
def transport():
    return PhonyTransport()


class PhonyPythonObjectCReg:

    def __init__(self):
        self._phony_servant = None

    def set_phony_servant(self, fn):
        self._phony_servant = fn

    def invite(self, servant_ref):
        return self._phony_servant


@mark.service
def pyobj_creg():
    return PhonyPythonObjectCReg()


def _return_str_list(phony_param):
    return [
        mosaic.put("Sample result string"),
        ]


def _raise_happ_error(phony_param):
    raise htypes.rpc_endpoint_tests.sample_error("sample error message")


def _raise_non_happ_error(phony_param):
    raise RuntimeError("Sample non-happ error")


def _run_test_with_servant(servant_fn):
    # rpc_endpoint.pyobj_creg.set_phony_servant(servant_fn)
    sender_identity = generate_rsa_identity(fast=True)
    rpc_request = htypes.rpc.request(
        request_id='phony request id',
        servant_ref=mosaic.put('phony servant'),
        params=(
            htypes.rpc.param('phony_param', mosaic.put('phony param')),
            ),
        )
    request = Request(
        receiver_identity=None,
        sender=None,
        ref_list=[mosaic.put(rpc_request)],
        )
    endpoint = rpc_endpoint_factory()
    endpoint.process(request)


def test_str_list_response():
    _run_test_with_servant(_return_str_list)


def test_happ_error():
    _run_test_with_servant(_raise_happ_error)


def test_non_happ_error():
    _run_test_with_servant(_raise_non_happ_error)
