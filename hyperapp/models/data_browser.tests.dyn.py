from . import htypes
from .tested.code import data_browser


def test_browse_current_model():
    piece_1 = htypes.data_browser_tests.sample_model_1()
    data_browser.browse_current_model(piece_1)
    piece_2 = htypes.data_browser_tests.sample_model_2()
    data_browser.browse_current_model(piece_2)
