from . import htypes
from .code.mark import mark
from .code.context import Context
from .tested.code import show_current_context


@mark.fixture
def piece():
    return htypes.show_current_context.model(
        items=(
            htypes.show_current_context.item(
                name="Sample name",
                value="Sample value",
                title="Sample value title",
                ),
            ),
        )


def test_model(piece):
    result = show_current_context.current_context_model(piece)
    assert type(result) in {list, tuple}


def test_show_current_context_command():
    ctx = Context(sample_context=12345)
    piece = show_current_context.show_current_context(ctx)
    assert piece
    assert piece.items[0].name == 'sample_context'


def test_formatter(piece):
    title = show_current_context.format_model(piece)
    assert type(title) is str
