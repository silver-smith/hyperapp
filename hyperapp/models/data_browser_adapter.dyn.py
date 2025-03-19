from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark


class DataBrowserViewDataAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx):
        data = web.summon(model.data)
        return cls(data)

    def __init__(self, data):
        self._data = data

    @property
    def model(self):
        return self._data

    def get_text(self):
        return str(self._data)

    def text_to_value(self, text):
        return text

    def value_changed(self, new_value):
        if new_value == self._text:
            return
        log.debug("Data browser view data adapter: Ignoring new value: %r", new_value)


@mark.view_factory.model_t
def data_browser_data_view(piece, adapter=None):
    if adapter is None:
        adapter = htypes.data_browser.record_data_adapter()
    return htypes.line_edit.readonly_view(
        adapter=mosaic.put(adapter),
        )
