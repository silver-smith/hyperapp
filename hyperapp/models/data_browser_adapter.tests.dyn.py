from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import data_browser_adapter


@mark.fixture
def record_view():
    data = "Sample string"
    return htypes.data_browser.record_view(
        data=mosaic.put(data),
        )


def test_adapter(record_view):
    ctx = Context()
    model = record_view
    piece = htypes.data_browser.record_data_adapter()
    adapter = data_browser_adapter.DataBrowserViewDataAdapter.from_piece(piece, model, ctx)
    assert type(adapter.get_text()) is str


def test_data_view_factory(record_view):
    view = data_browser_adapter.data_browser_data_view(record_view, adapter=None)
    assert view
