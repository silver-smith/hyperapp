from .code.context import Context
from .tested.code import show_current_context


def test_show_current_context():
    ctx = Context(sample_context=12345)
    result = show_current_context.show_current_context(ctx)
    assert result
    assert result[0].name == 'sample_context'
