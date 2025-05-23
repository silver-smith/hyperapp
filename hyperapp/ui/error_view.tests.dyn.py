from .code.context import Context
from .fixtures import visualizer_fixtures
from .tested.code import error_view


async def test_error_view(error_view):
    ctx = Context()
    exception = RuntimeError("Shit happens")
    model, model_ctx, view = await error_view(exception, ctx)
    assert model
    assert view
