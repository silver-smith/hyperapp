from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import data_browser_adapter


def test_data_view_factory():
    data = "Sample string"
    piece = htypes.data_browser.record_view(
        data=mosaic.put(data),
        )
    view = data_browser_adapter.data_browser_data_view(piece, adapter=None)
    assert view
