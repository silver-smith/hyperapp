from . import htypes
from .tested.code import str_adapter


def test_adapter():
    text = "Sample value"
    piece = htypes.str_adapter.static_str_adapter(text)
    adapter = str_adapter.StaticStrAdapter.from_piece(piece)
    assert adapter.get_text() == text
