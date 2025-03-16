from . import htypes
from .tested.code import model_list
from .code.mark import mark


@mark.fixture
def piece():
    return htypes.model_list.model()


def test_model(piece):
    item_list = model_list.model_list_model(piece)
    assert type(item_list) is list


def test_open():
    piece = model_list.open_model_list()
    assert piece


def test_format_model(piece):
    title = model_list.format_model(piece)
    assert type(title) is str
