from . import htypes
from .code.mark import mark
from .tested.code import sample_crud


def test_open():
    piece = sample_crud.open_crud_sample()
    assert isinstance(piece, htypes.sample_crud.model)


@mark.fixture
def piece():
    return htypes.sample_crud.model()


def test_list(piece):
    items = sample_crud.list_crud_sample(piece)
    assert items
    assert isinstance(items[0], htypes.sample_crud.item)


def test_get(piece):
    current_item = htypes.sample_crud.item(2, "item#2", "Crud sample item #2")
    edit_item = sample_crud.get_crud_sample(piece, current_item)


def test_update(piece):
    value = htypes.sample_crud.edit_item(2, "item#2-new", "New crud sample item #2")
    sample_crud.update_crud_sample(piece, value)
