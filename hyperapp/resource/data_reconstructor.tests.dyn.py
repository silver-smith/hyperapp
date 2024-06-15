from . import htypes
from .tested.code import data_reconstructor


def test_reconstruct_data():
    piece = htypes.data_reconstructor_tests.sample_empty_record()
    res = data_reconstructor.data_to_piece(piece)
    assert res
