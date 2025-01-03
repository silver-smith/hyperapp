from unittest.mock import MagicMock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import lcs_layers_view


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def layer_1_d():
    return htypes.lcs_layers_view_tests.layer_1_d()


@mark.fixture
def lcs(layer_1_d):
    dir_1 = {
        htypes.lcs_layers_view_tests.sample_1_d(),
        }
    dir_2 = {
        htypes.lcs_layers_view_tests.sample_1_d(),
        pyobj_creg.actor_to_piece(htypes.lcs_layers_view_tests.sample_2_d),
        }
    items = [
        (layer_1_d, dir_1, htypes.lcs_layers_view_tests.sample_model_1()),
        (layer_1_d, dir_2, htypes.lcs_layers_view_tests.sample_model_2()),
        ]
    mock = MagicMock()
    mock.__iter__.return_value = items
    mock.layers.return_value = [layer_1_d]
    return mock


@mark.fixture
def piece():
    return htypes.lcs_layers_view.view()


def test_layers_view(layer_1_d, lcs, piece):
    item_list = lcs_layers_view.lcs_layers_view(piece, lcs)
    assert item_list == [
        htypes.lcs_layers_view.item('layer_1', mosaic.put(layer_1_d)),
        ], item_list


def test_open():
    piece = htypes.lcs_view.view(filter=())
    view = lcs_layers_view.lcs_open_layers(piece)
    assert view


def test_selector_get():
    value = htypes.lcs_layers_view.layer(
        d=mosaic.put(htypes.lcs_layers_view_tests.sample_1_d()),
        )
    piece = lcs_layers_view.layer_get(value)
    assert isinstance(piece, htypes.lcs_layers_view.view)


def test_selector_put():
    piece = htypes.lcs_layers_view.view()
    current_item = htypes.lcs_layers_view.item(
        name="<unused>",
        d=mosaic.put(htypes.lcs_layers_view_tests.layer_2_d()),
        )
    value = lcs_layers_view.layer_put(piece, current_item)
    assert isinstance(value, htypes.lcs_layers_view.layer)


def test_layout(lcs, ctx, piece):
    view = lcs_layers_view.layer_selector_layout(piece, lcs, ctx)
    assert view


def test_select(lcs, piece):
    current_item = htypes.lcs_layers_view.item(
        name="<unused>",
        d=mosaic.put(htypes.lcs_layers_view_tests.layer_2_d()),
        )
    lcs_layers_view.select_layer(piece, current_item, lcs)
    lcs.move.assert_called_once()
