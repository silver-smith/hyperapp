from unittest.mock import MagicMock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import lcs_view


@mark.fixture
def lcs():
    dir_1 = {
        htypes.lcs_view_tests.sample_1_d(),
        }
    dir_2 = {
        htypes.lcs_view_tests.sample_1_d(),
        pyobj_creg.actor_to_piece(htypes.lcs_view_tests.sample_2_d),
        }
    
    items = [
        (dir_1, htypes.lcs_view_tests.sample_model_1()),
        (dir_2, htypes.lcs_view_tests.sample_model_2()),
        ]
    mock = MagicMock()
    mock.__iter__.return_value = items
    return mock


@mark.fixture
def piece():
    return htypes.lcs_view.view()


def test_view(lcs, piece):
    item_list = lcs_view.lcs_view(piece, lcs)
    assert type(item_list) is list
    assert len(item_list) == 2


def test_open_piece(data_to_ref, piece):
    current_item = htypes.lcs_view.item(
        dir=(data_to_ref(htypes.lcs_view_tests.sample_1_d()),),
        piece=mosaic.put(htypes.lcs_view_tests.sample_model_1()),
        dir_str="<unused>",
        piece_str="<unused>",
        )
    browser_piece = lcs_view.lcs_open_piece(piece, current_item)
    assert browser_piece


def test_open_view():
    piece = lcs_view.open_lcs_view()
    assert piece
