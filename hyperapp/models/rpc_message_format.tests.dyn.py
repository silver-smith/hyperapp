from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import rpc_message_format


def _sample_fn():
    pass


@mark.fixture
def rpc_target():
    return htypes.rpc.function_target(
        servant_ref=pyobj_creg.actor_to_ref(_sample_fn),
        params=(
            htypes.rpc.param('param_1', mosaic.put('value-1')),
            htypes.rpc.param('param_2', mosaic.put('value-2')),
            ),
        )


def test_rpc_request(rpc_target):
    piece = htypes.rpc.request(
        request_id='abc-def',
        target=mosaic.put(rpc_target),
        )
    title = rpc_message_format.format_rpc_request(piece)
    assert type(title) is str


def test_rpc_response():
    result = "Sample result"
    piece = htypes.rpc.response(
        request_id='abc-def',
        result_ref=mosaic.put(result),
        )
    title = rpc_message_format.format_rpc_response(piece)
    assert type(title) is str


def test_rpc_error_response():
    exception = "Sample exception"
    piece = htypes.rpc.error_response(
        request_id='abc-def',
        exception_ref=mosaic.put(exception),
        )
    title = rpc_message_format.format_rpc_error_response(piece)
    assert type(title) is str


def test_rpc_function_target(rpc_target):
    title = rpc_message_format.format_rpc_function_target(rpc_target)
    assert type(title) is str


def test_rpc_system_fn_target():
    fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=(),
        service_params=(),
        )
    piece = htypes.rpc.system_fn_target(
        fn=mosaic.put(fn),
        params=(
            htypes.rpc.param('param_1', mosaic.put('value-1')),
            htypes.rpc.param('param_2', mosaic.put('value-2')),
            ),
        )
    title = rpc_message_format.format_rpc_system_fn_target(piece)
    assert type(title) is str
