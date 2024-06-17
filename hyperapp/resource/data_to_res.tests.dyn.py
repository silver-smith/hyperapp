from . import htypes
from .services import (
    pyobj_creg,
    )
from .tested.code import data_to_res
from .tested.services import data_to_res


def test_data_to_res():
    piece = htypes.data_to_res_tests.sample_empty_record()
    res = data_to_res(piece)
    piece_2 = pyobj_creg.animate(res)
    assert piece_2 == piece
