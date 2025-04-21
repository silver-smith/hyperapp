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


def test_remove_idx():
    piece = htypes.diff.remove_idx(
        idx=123,
        )
    diff = list_diff.ListDiffRemoveIdx.from_piece(piece)
    assert diff.piece == piece


def test_remove_key():
    piece = htypes.diff.remove_key(
        key=mosaic.put('123'),
        )
    diff = list_diff.ListDiffRemoveKey.from_piece(piece)
    assert diff.piece == piece
