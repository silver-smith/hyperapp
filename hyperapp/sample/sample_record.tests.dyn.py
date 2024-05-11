from . import htypes
from .tested.code import sample_record


def test_sample_record():
    piece = htypes.sample_record.sample_record()
    value = sample_record.sample_record(piece)
    assert value
