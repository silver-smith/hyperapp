from unittest.mock import MagicMock

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import lcs_dirs_view


@mark.fixture
def layer_d():
    return htypes.lcs_dirs_view_tests.layer_d()


@mark.fixture
def lcs(layer_d):
    dir_1 = {
        htypes.lcs_dirs_view_tests.sample_1_d('id'),
        }
    dir_2 = {
        htypes.lcs_dirs_view_tests.sample_1_d('name'),
        }
    dir_3 = {
        htypes.lcs_dirs_view_tests.sample_1_d('name'),
        pyobj_creg.actor_to_piece(htypes.lcs_dirs_view_tests.sample_2_d),
        }
    items = [
        (layer_d, dir_1, htypes.lcs_dirs_view_tests.sample_model_1()),
        (layer_d, dir_2, htypes.lcs_dirs_view_tests.sample_model_2()),
        (layer_d, dir_3, "some string"),
        ]
    mock = MagicMock()
    mock.__iter__.return_value = items
    return mock


@mark.fixture
def piece():
    return htypes.lcs_dirs_view.view()


def test_view(lcs, piece):
    item_list = lcs_dirs_view.lcs_dirs_view(piece, lcs)
    assert type(item_list) is list
    assert len(item_list) == 3


def test_open_items(data_to_ref, piece):
    d = htypes.lcs_dirs_view_tests.sample_1_d('name')
    current_item = htypes.lcs_dirs_view.item(
        d=data_to_ref(d),
        d_str="<unused>",
        item_count=1,
        )
    lcs_view = lcs_dirs_view.lcs_dirs_items(piece, current_item)
    assert isinstance(lcs_view, htypes.lcs_view.view)
    assert lcs_view.filter


def test_open():
    lcs_view = htypes.lcs_view.view(filter=())
    piece = lcs_dirs_view.lcs_open_dirs(lcs_view)
    assert piece
