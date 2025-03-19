from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark


@mark.view_factory.model_t
def data_browser_data_view(piece, adapter=None):
    if adapter is None:
        adapter = htypes.data_browser.record_data_adapter()
    return htypes.line_edit.readonly_view(
        adapter=mosaic.put(adapter),
        )
