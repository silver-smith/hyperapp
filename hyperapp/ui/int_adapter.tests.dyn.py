from . import htypes
from .code.context import Context
from .tested.code import int_adapter


def test_adapter():
    ctx = Context()
    value = 12345
    piece = htypes.int_adapter.int_adapter()
    adapter = int_adapter.IntAdapter.from_piece(piece, value, ctx)
    assert adapter.get_text() == str(value)
