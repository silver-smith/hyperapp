from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .tested.code import lcs_layer_selector


@mark.fixture
def lcs():
    mock = Mock()
    mock.get.return_value = None
    return mock


@mark.fixture
def piece():
    return htypes.lcs_view.layer_selector(
        source_layer_d=mosaic.put(htypes.lcs_layer_selector_tests.layer_1_d()),
        dir=(mosaic.put(htypes.lcs_layer_selector_tests.sample_d()),),
        )


def test_layout(lcs, piece):
    view = lcs_layer_selector.layer_selector_layout(piece, lcs)
    assert view


def test_select(lcs, piece):
    current_item = htypes.lcs_view.layer_item(
        name="<unused>",
        d=mosaic.put(htypes.lcs_layer_selector_tests.layer_2_d()),
        )
    lcs_layer_selector.select_layer(piece, current_item, lcs)
    lcs.move.assert_called_once()
