from . import htypes
from .code.mark import mark
from .tested.code import fs


@mark.fixture
def piece():
    return htypes.fs.model()


def test_model(piece):
    path = ['etc']
    item_list = fs.fs_model(piece, path)
    assert type(item_list) is list


def test_open():
    piece = fs.open_fs()
    assert piece
