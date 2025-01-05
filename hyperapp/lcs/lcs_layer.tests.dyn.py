from unittest.mock import MagicMock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import lcs_layer


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def layer_1_d():
    return htypes.lcs_layer_tests.layer_1_d()


@mark.fixture
def lcs(layer_1_d):
    dir_1 = {
        htypes.lcs_layer_tests.sample_1_d(),
        }
    dir_2 = {
        htypes.lcs_layer_tests.sample_1_d(),
        pyobj_creg.actor_to_piece(htypes.lcs_layer_tests.sample_2_d),
        }
    items = [
        (layer_1_d, dir_1, htypes.lcs_layer_tests.sample_model_1()),
        (layer_1_d, dir_2, htypes.lcs_layer_tests.sample_model_2()),
        ]
    mock = MagicMock()
    mock.__iter__.return_value = items
    mock.layers.return_value = [layer_1_d]
    return mock


@mark.fixture
def piece():
    return htypes.lcs_layer.model()


def test_model(layer_1_d, lcs, piece):
    item_list = lcs_layer.lcs_layers_model(piece, lcs)
    assert item_list == [
        htypes.lcs_layer.item('layer_1', mosaic.put(layer_1_d)),
        ], item_list


def test_open():
    piece = htypes.lcs_view.view(filter=())
    view = lcs_layer.lcs_open_layers(piece)
    assert view


def test_selector_get():
    value = htypes.lcs_layer.layer(
        d=mosaic.put(htypes.lcs_layer_tests.sample_1_d()),
        )
    piece = lcs_layer.layer_get(value)
    assert isinstance(piece, htypes.lcs_layer.model)


def test_selector_put():
    piece = htypes.lcs_layer.model()
    current_item = htypes.lcs_layer.item(
        name="<unused>",
        d=mosaic.put(htypes.lcs_layer_tests.layer_2_d()),
        )
    value = lcs_layer.layer_put(piece, current_item)
    assert isinstance(value, htypes.lcs_layer.layer)
