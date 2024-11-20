from . import htypes
from .code.mark import mark
from .tested.code import sample_list_crud


@mark.fixture
def piece():
    return htypes.sample_list.sample_list()


def test_get(piece):
    edit_item = sample_list_crud.sample_list_get(piece, 2)


def test_update(piece):
    value = htypes.sample_list_crud.form_item(2, "Second sample - new")
    sample_list_crud.sample_list_update(piece, 2, value)
