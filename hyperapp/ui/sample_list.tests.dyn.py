from . import htypes
from .tested.code import sample_list


def test_sample_list():
    value = sample_list.sample_list(htypes.sample_list.sample_list())
    assert value


async def test_open_sample_list_command():
    piece = await sample_list.open_sample_fn_list()
    assert isinstance(piece, htypes.sample_list.sample_list), repr(piece)
