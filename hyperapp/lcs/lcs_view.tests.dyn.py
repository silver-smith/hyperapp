from unittest.mock import MagicMock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .fixtures import feed_fixtures
from .tested.code import lcs_view


@mark.fixture
def layer_1_d():
    return htypes.lcs_view_tests.layer_1_d()


@mark.fixture
def lcs(layer_1_d):
    dir_1 = {
        htypes.lcs_view_tests.sample_1_d(),
        }
    dir_2 = {
        htypes.lcs_view_tests.sample_1_d(),
        pyobj_creg.actor_to_piece(htypes.lcs_view_tests.sample_2_d),
        }
    items = [
        (layer_1_d, dir_1, htypes.lcs_view_tests.sample_model_1()),
        (layer_1_d, dir_2, htypes.lcs_view_tests.sample_model_2()),
        ]
    mock = MagicMock()
    mock.__iter__.return_value = items
    mock.layers.return_value = [layer_1_d]
    return mock


@mark.fixture
def piece():
    return htypes.lcs_view.view(filter=())


def test_view(lcs, piece):
    item_list = lcs_view.lcs_view(piece, lcs)
    assert type(item_list) is list
    assert len(item_list) == 2


def test_filtered_view(lcs):
    piece = htypes.lcs_view.view(filter=(
        pyobj_creg.actor_to_ref(htypes.lcs_view_tests.sample_2_d),
        ))
    item_list = lcs_view.lcs_view(piece, lcs)
    assert type(item_list) is list
    assert len(item_list) == 1, item_list


async def test_remove(layer_1_d, piece, lcs, feed_factory):
    feed = feed_factory(piece)
    current_item = htypes.lcs_view.item(
        layer_d=mosaic.put(layer_1_d),
        layer="<unused>",
        dir=(mosaic.put(htypes.lcs_view_tests.sample_1_d()),),
        piece=mosaic.put(htypes.lcs_view_tests.sample_model_1()),
        dir_str="<unused>",
        piece_str="<unused>",
        )
    await lcs_view.lcs_remove(piece, 0, current_item, lcs)
    lcs.remove.assert_called_once()
    await feed.wait_for_diffs(count=1)


def test_open_piece(layer_1_d, piece):
    current_item = htypes.lcs_view.item(
        layer_d=mosaic.put(layer_1_d),
        layer="<unused>",
        dir=(mosaic.put(htypes.lcs_view_tests.sample_1_d()),),
        piece=mosaic.put(htypes.lcs_view_tests.sample_model_1()),
        dir_str="<unused>",
        piece_str="<unused>",
        )
    browser_piece = lcs_view.lcs_open_piece(piece, current_item)
    assert browser_piece


def test_open_view():
    piece = lcs_view.open_lcs_view()
    assert piece


def test_get_layer(layer_1_d, piece):
    layer = lcs_view.lcs_get_layer(
        piece,
        layer_d=mosaic.put(layer_1_d),
        )
    assert isinstance(layer, htypes.lcs_layer.layer)


def test_move(lcs, piece, layer_1_d):
    dir = (mosaic.put(htypes.lcs_view_tests.sample_1_d()),)
    value = htypes.lcs_layer.layer(
        layer_d=mosaic.put(htypes.lcs_layer_tests.layer_2_d()),
        )
    lcs_view.lcs_move_to_another_layer(piece, dir, mosaic.put(layer_1_d), value, lcs)
    lcs.move.assert_called_once()
