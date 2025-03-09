import logging
import weakref
from functools import partial

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.view import View

log = logging.getLogger(__name__)


class TextInput:

    def __init__(self, view, widget):
        self._view = view
        self._widget_wr = weakref.ref(widget)

    def get_value(self):
        widget = self._widget_wr()
        if not widget:
            raise RuntimeError(f"Text input: widget for {self._view} is gone")
        return self._view.get_value(widget)


class ViewTextView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(piece.adapter, adapter)

    def __init__(self, adapter_ref, adapter):
        super().__init__()
        self._adapter_ref = adapter_ref
        self._adapter = adapter

    @property
    def piece(self):
        return htypes.text.readonly_view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextBrowser()
        w.setPlainText(self._adapter.get_text())
        return w

    def widget_state(self, widget):
        return htypes.text.state(text=self.get_plain_text(widget))

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model_state=self._model_state(widget),
            input=TextInput(self, widget),
            )

    def _model_state(self, widget):
        return self.get_value(widget)

    def get_plain_text(self, widget):
        return widget.toPlainText()

    def get_value(self, widget):
        text = self.get_plain_text(widget)
        return self._adapter.text_to_value(text)


class EditTextView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(piece.adapter, adapter)

    def __init__(self, adapter_ref, adapter):
        super().__init__()
        self._adapter_ref = adapter_ref
        self._adapter = adapter

    @property
    def piece(self):
        return htypes.text.edit_view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextEdit()
        if state:
            text = state.text
        else:
            text = self._adapter.get_text()
        w.setPlainText(text)
        w.textChanged.connect(partial(self._on_text_changed, w))
        return w

    def widget_state(self, widget):
        return htypes.text.state(text=self.get_text(widget))

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model_state=self._model_state(widget),
            input=TextInput(self, widget),
            )

    def _model_state(self, widget):
        return self.get_value(widget)

    def get_text(self, widget):
        return widget.toPlainText()

    def get_value(self, widget):
        text = self.get_text(widget)
        return self._adapter.text_to_value(text)

    def _on_text_changed(self, widget):
        text = self.get_text(widget)
        self._adapter.value_changed(text)


@mark.view_factory.model_t
def text_view(piece, adapter=None):
    if adapter is None:
        adapter = htypes.str_adapter.static_str_adapter()
    return htypes.text.readonly_view(
        adapter=mosaic.put(adapter),
        )


@mark.view_factory.model_t
def text_edit(piece, adapter=None):
    if adapter is None:
        adapter = htypes.str_adapter.static_str_adapter()
    return htypes.text.edit_view(
        adapter=mosaic.put(adapter),
        )
