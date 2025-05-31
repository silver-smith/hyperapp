from . import htypes
from .tested.code import sample_record


def test_sample_record():
    piece = htypes.sample_record.sample_record()
    value = sample_record.sample_record(piece)
    assert value


def test_open():
    piece = sample_record.open_sample_fn_record()
    assert piece


def test_apply():
    piece = htypes.sample_record.sample_record()
    item = htypes.sample_record.item(12345, "Sample title")
    result = sample_record.apply(piece, item)
    assert type(result) is str
