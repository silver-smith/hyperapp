from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .tested.code import data_to_res as data_to_res_module


def test_data_to_res(data_to_res):
    piece = htypes.data_to_res_tests.sample_empty_record()
    res = data_to_res(piece)
    piece_2 = pyobj_creg.animate(res)
    assert piece_2 == piece


def test_non_empty_record(data_to_res):
    sample_value = htypes.data_to_res_tests.sample_value()
    piece = htypes.data_to_res_tests.sample_non_empty_record(
        string_field='sample string',
        ref_field=mosaic.put(sample_value),
        )
    res = data_to_res(piece)
    piece_2 = pyobj_creg.animate(res)
    assert piece_2 == piece
