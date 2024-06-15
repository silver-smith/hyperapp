from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .tested.code import data_reconstructor


def test_empty_record():
    piece = htypes.data_reconstructor_tests.sample_empty_record()
    res = data_reconstructor.data_to_piece(piece)
    assert res
    piece_2 = pyobj_creg.animate(res)
    assert piece_2 == piece


# def test_non_empty_record():
#     sample_value = htypes.data_reconstructor_tests.sample_value()
#     piece = htypes.data_reconstructor_tests.sample_non_empty_record(
#         string_field='sample string',
#         ref_field=mosaic.put(sample_value),
#         )
#     res = data_reconstructor.data_to_piece(piece)
#     assert res
#     piece_2 = pyobj_creg.animate(res)
#     assert piece_2 == piece
