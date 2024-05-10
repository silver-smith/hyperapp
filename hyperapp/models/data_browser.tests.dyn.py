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
        sample_list=(11, 22, 33),
        inner=htypes.data_browser_tests.inner_data("Sample inner text"),
        value=mosaic.put("Sample value"),
        )
    piece = htypes.data_browser.data_browser(
        data=mosaic.put(data),
        )
    result = data_browser.browse(piece)
    assert len(result) == 4
    assert isinstance(result[0], htypes.data_browser.item)
    assert result[0].name == 'name'
    assert result[0].type == 'str'
    assert result[0].value == data.name
    assert result[1].name == 'sample_list'


def test_open():
    data = htypes.data_browser_tests.sample_data(
        name="Sample name",
        sample_list=(11, 22, 33),
        inner=htypes.data_browser_tests.inner_data("Sample inner text"),
        value=mosaic.put("Sample value"),
        )
    piece = htypes.data_browser.data_browser(
        data=mosaic.put(data),
        )
    current_item = htypes.data_browser.item(
        name="inner",
        type="",
        value="",
        )
    result = data_browser.open(piece, current_item)
    assert isinstance(result, htypes.data_browser.data_browser)
