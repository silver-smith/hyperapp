from .code.mark import mark


@mark.fixture
async def error_view(x, ctx):
    raise RuntimeError(f"Error view is called: {x}") from x
