from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .tested.code import list_diff


def test_append():
    item = htypes.list_diff_tests.sample_item(
        id='123',
        )
    piece = htypes.diff.append(
        item=mosaic.put(item),
        )
    diff = list_diff.ListDiffAppend.from_piece(piece)
    assert diff.piece == piece
