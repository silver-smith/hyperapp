from . import htypes
from .tested.services import (
    data_to_res,
    )


def test_data_to_res():
    piece = htypes.data_to_res_tests.sample_empty_record()
    res = data_to_res(piece)
    assert res
