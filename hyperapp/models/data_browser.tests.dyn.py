from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import data_browser


def test_browse_current_model():
    piece_1 = htypes.data_browser_tests.sample_model_1()
    result_1 = data_browser.browse_current_model(piece_1)
    assert isinstance(result_1, htypes.data_browser.data_browser)
    piece_2 = htypes.data_browser_tests.sample_model_2()
    result_2 = data_browser.browse_current_model(piece_2)
    assert isinstance(result_2, htypes.data_browser.data_browser)


def test_browser():
    data = htypes.data_browser_tests.sample_data(
        name="Sample name",
        value=mosaic.put("Sample value"),
        )
    piece = htypes.data_browser.data_browser(
        data=mosaic.put(data),
        )
    result = data_browser.browse(piece)
