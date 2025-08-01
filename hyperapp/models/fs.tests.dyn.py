from . import htypes
from .code.mark import mark
from .tested.code import fs


@mark.fixture
def piece():
    return htypes.fs.model()


def test_open():
    piece = fs.open_fs()
    assert isinstance(piece, htypes.fs.model)


def test_model(piece):
    parent = htypes.fs.item(
        name='<unused>',
        size=None,
        )
    path = ['etc']
    item_list = fs.fs_model(piece, path)
    assert type(item_list) is list
    assert item_list
    assert isinstance(item_list[0], htypes.fs.item)


def test_formatter(piece):
    title = fs.format_model(piece)
    assert type(title) is str


def test_get(piece):
    value = htypes.fs.path(
        parts=('tmp', 'sample'),
        )
    model, current_path = fs.fs_get(value)
    assert model == piece
    assert current_path == ('tmp', 'sample')


def test_pick(piece):
    current_path = ('tmp', 'sample')
    value = fs.fs_pick(piece, current_path)
    assert value == htypes.fs.path(
        parts=('tmp', 'sample'),
        )
