from . import htypes
from .code.context import Context
from .tested.code import str_adapter


def test_adapter():
    ctx = Context()
    text = "Sample value"
    piece = htypes.str_adapter.static_str_adapter()
    adapter = str_adapter.StaticStrAdapter.from_piece(piece, text, ctx)
    assert adapter.get_text() == text
