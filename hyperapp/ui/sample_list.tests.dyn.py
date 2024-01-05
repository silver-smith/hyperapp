import asyncio

from . import htypes
from .tested.code import sample_list


def test_sample_list():
    value = sample_list.sample_list(htypes.sample_list.sample_list())
    assert value


def test_open_sample_list_command():
    piece = asyncio.run(sample_list.open_sample_fn_list())
    assert isinstance(piece, htypes.sample_list.sample_list), repr(piece)
