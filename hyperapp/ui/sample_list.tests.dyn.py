from . import htypes
from .tested.code import sample_list


def test_sample_list():
    value = sample_list.sample_list(htypes.sample_list.sample_list())
    assert value
