from . import htypes
from .tested.code import sample_crud


def test_open():
    piece = sample_crud.open_crud_sample()
    assert isinstance(piece, htypes.sample_crud.model)


def test_list():
    piece = htypes.sample_crud.model()
    items = sample_crud.list_crud_sample(piece)
    assert items
    assert isinstance(items[0], htypes.sample_crud.item)
